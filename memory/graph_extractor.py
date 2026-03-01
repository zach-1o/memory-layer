"""
Graph Extraction Worker — async Gemini 2.5 Flash triple extractor.

Extracts directional relationship triples from observation content:
  (Subject, RELATION, Object)

Mirrors the compression worker pattern:
  - Trigger: after observation batch or session end
  - Model: Gemini 2.5 Flash (cheapest, fastest, structured JSON)
  - Run in background — NEVER block MCP responses
  - Fallback: CO_OCCURS edges remain if extraction fails
"""

import os
import json
import asyncio
import logging
from typing import Optional

from dotenv import load_dotenv

from namespacing.tenant import Tenant
from memory import episodic, graph

load_dotenv()

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are a high-fidelity knowledge graph extraction engine.

Task: Extract relationship triples (subject, relation, object) from the provided coding session observation.

VALID RELATIONSHIPS (STRICTLY use ONLY these):
- CALLS: function/method invokes another
- READS: reads a file or variable
- WRITES: writes/modifies a file or variable
- IMPORTS: imports/uses a module or package
- CONTAINS: file contains code item, class contains method
- LOCATED_IN: entity is defined within a file/directory
- SENDS_TO: data flows from A to B
- TRIGGERS: action A causes action B
- RETURNS: function returns a value/type
- CREATES: creates a new entity
- FIXES: a bug fix targets something
- USES: generic usage relationship
- DEPENDS_ON: structural dependency

RULES:
1. Extract 3-10 high-value triples.
2. Names must be concise (e.g., 'main.py' or 'AuthService', not full paths).
3. If specific entities are provided, focus on their interactions.
4. Output MUST be a valid JSON array of objects.

OBSERVATION:
{raw_content}

ENTITIES MENTIONED: {entities}

OUTPUT (JSON array):"""


async def extract_triples(
    raw_content: str,
    entities: str,
    api_key: Optional[str] = None,
) -> list[dict]:
    """
    Extract relationship triples from observation text using Gemini 2.5 Flash.
    Returns list of {"subject": str, "relation": str, "object": str}.
    """
    key = api_key or os.getenv("GOOGLE_API_KEY", "")
    if not key:
        logger.warning("GOOGLE_API_KEY not set — skipping graph extraction")
        return []

    prompt = EXTRACTION_PROMPT.format(
        raw_content=raw_content,
        entities=entities,
    )

    try:
        from google import genai

        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "temperature": 0.1,
                "max_output_tokens": 4096,
                "response_mime_type": "application/json",
            },
        )

        text = response.text.strip()
        logger.info(f"GEMINI RAW TEXT: {text!r}")
        triples = json.loads(text)
        if not isinstance(triples, list):
            logger.warning(f"Gemini returned non-list: {type(triples)}")
            return []

        # Validate and normalize
        valid = []
        for t in triples:
            subject, relation, obj = None, None, None
            if isinstance(t, dict) and "subject" in t and "relation" in t and "object" in t:
                subject, relation, obj = t["subject"], t["relation"], t["object"]
            elif isinstance(t, list) and len(t) == 3:
                subject, relation, obj = t[0], t[1], t[2]
            
            if subject and relation and obj:
                rel = str(relation).upper().replace(" ", "_")
                valid.append({
                    "subject": str(subject).strip(),
                    "relation": rel,
                    "object": str(obj).strip(),
                })

        logger.info(f"Extracted {len(valid)} triples from observation")
        return valid

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"Graph extraction failed: {e}")
        return []


async def extract_and_apply(tenant: Tenant, obs_id: str, raw_content: str, entities: str) -> int:
    """
    Extract triples from a single observation and apply them to the graph.
    Returns number of edges added.
    """
    # Check if already extracted by looking for a graph edge with this obs as source
    existing = graph.get_all_edges(tenant)
    already_done = any(
        e.get("metadata", {}).get("source_obs") == obs_id
        for e in existing
        if isinstance(e.get("metadata"), dict)
    )
    if already_done:
        logger.info(f"Skipping already-extracted obs {obs_id}")
        return 0

    triples = await extract_triples(raw_content, entities)

    count = 0
    for t in triples:
        try:
            # Determine node types from context
            graph.add_edge(
                tenant,
                source=t["subject"],
                target=t["object"],
                relationship=t["relation"],
                metadata={"source_obs": obs_id, "extraction": "gemini-flash"},
            )
            count += 1
        except ValueError as e:
            logger.warning(f"Invalid edge relationship: {e}. Falling back to RELATES_TO.")
            try:
                graph.add_edge(
                    tenant,
                    source=t["subject"],
                    target=t["object"],
                    relationship="RELATES_TO",
                    metadata={"source_obs": obs_id, "extraction": "gemini-flash", "original_relation": t["relation"]},
                )
                count += 1
            except Exception as outer_e:
                logger.error(f"Fallback edge failed {t}: {outer_e}")
        except Exception as e:
            logger.error(f"Failed to apply edge {t}: {e}")

    if count > 0:
        logger.info(f"Applied {count} extracted edges for observation {obs_id}")

    return count


async def extract_batch(tenant: Tenant, batch_size: int = 5) -> int:
    """
    Process a batch of recent observations for graph extraction.
    Mirrors compression.compress_batch pattern.
    Returns total edges added.
    """
    # Get recent uncompressed observations (they haven't been processed yet)
    recent = episodic.get_recent(tenant, limit=batch_size)

    if not recent:
        return 0

    total = 0
    for obs in recent:
        try:
            entities_raw = obs.get("entities_mentioned", "[]")
            if isinstance(entities_raw, list):
                entities_raw = json.dumps(entities_raw)

            count = await extract_and_apply(
                tenant,
                obs_id=obs.get("obs_id") or obs.get("id", ""),
                raw_content=obs.get("raw_content", ""),
                entities=entities_raw,
            )
            total += count
        except Exception as e:
            logger.error(f"Failed to extract from observation: {e}")
            continue

    return total
