"""
Compression Worker — async Claude Haiku summarizer.

Takes raw observations and compresses them to ≤200-token summaries.
Extracts: core intent, files touched, entities created/modified, decisions made.

Rules from agent.md:
  - Trigger: after session end OR after 5+ raw observations batch up
  - Model: Claude Haiku (cheapest, fastest)
  - Output: ≤ 200 tokens
  - Run in background — NEVER block MCP responses
"""

import os
import asyncio
import logging
from typing import Optional

from anthropic import AsyncAnthropic
from dotenv import load_dotenv

from namespacing.tenant import Tenant
from memory import episodic, semantic

load_dotenv()

logger = logging.getLogger(__name__)

COMPRESSION_PROMPT = """You are a memory compression engine. Compress the following raw observation into a concise summary of ≤200 tokens.

Extract and preserve:
1. Core intent — what was the user/agent trying to do?
2. Files touched — which files were read, created, or modified?
3. Entities — functions, classes, variables created or modified
4. Decision made — what choice was made and why?

Raw observation:
{raw_content}

Entities mentioned: {entities}

Respond with ONLY the compressed summary, no preamble."""


async def compress_observation(
    raw_content: str,
    entities: str,
    api_key: Optional[str] = None,
) -> str:
    """
    Compress a single raw observation using Claude Haiku.
    Returns the compressed summary string.
    """
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        logger.warning("No ANTHROPIC_API_KEY set, returning truncated content as summary")
        return raw_content[:500]

    client = AsyncAnthropic(api_key=key)

    try:
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": COMPRESSION_PROMPT.format(
                        raw_content=raw_content,
                        entities=entities,
                    ),
                }
            ],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Compression failed: {e}")
        # Fallback: truncated raw content (never block on compression failure)
        return raw_content[:500]


async def compress_batch(tenant: Tenant, batch_size: int = 5) -> int:
    """
    Compress a batch of unprocessed observations.
    Updates both the episodic log (summary) and semantic layer (embedding).

    Returns the number of observations compressed.
    """
    try:
        uncompressed = episodic.get_uncompressed(tenant, limit=batch_size)

        if not uncompressed:
            return 0

        count = 0
        for obs in uncompressed:
            try:
                summary = await compress_observation(
                    raw_content=obs["raw_content"],
                    entities=obs.get("entities_mentioned", "[]"),
                )

                # Estimate token count (~4 chars per token)
                token_count = len(summary) // 4

                # Update episodic log with compressed summary
                episodic.update_summary(tenant, obs["id"], summary, token_count)

                # Upsert into semantic store for vector search
                semantic.upsert_observation(
                    tenant,
                    obs_id=obs["id"],
                    summary=summary,
                    metadata={"entities": obs.get("entities_mentioned", "[]")},
                )

                count += 1
                logger.info(f"Compressed observation {obs['id']} ({token_count} tokens)")

            except Exception as e:
                logger.error(f"Failed to compress observation {obs['id']}: {e}")
                continue

        return count
    except Exception as e:
        logger.error(f"Global error in compress_batch background task for tenant {tenant.project_id}: {e}")
        return 0



def run_compression(tenant: Tenant, batch_size: int = 5) -> int:
    """
    Synchronous wrapper for compress_batch.
    Safe to call from non-async contexts.
    """
    return asyncio.run(compress_batch(tenant, batch_size))
