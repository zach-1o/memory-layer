import os
import json
import asyncio
from google import genai
from dotenv import load_dotenv

load_dotenv()

EXTRACTION_PROMPT = """You are a knowledge graph extraction engine for an AI coding assistant's memory system.
Given an observation from a coding session, extract relationship triples: (subject, relation, object).
VALID RELATIONS (use ONLY these):
- CALLS, READS, WRITES, IMPORTS, CONTAINS, LOCATED_IN, SENDS_TO, TRIGGERS, RETURNS, LOCKS, CREATES, FIXES, USES, DEPENDS_ON, EXTENDS

OBSERVATION:
Implemented Flappy Bird's physics engine. The Bird class uses a gravity constant of 0.6 and a jump impulse of -10. It checks for collisions with Pipe objects using the Rect intersection method. The GameLoop triggers the update() method on the Bird and every Pipe in the active list.

ENTITIES MENTIONED: ["Bird", "Pipe", "GameLoop", "physics engine"]

OUTPUT (Return ONLY a JSON array of objects with keys "subject", "relation", "object"):"""

async def test_extraction(model_name):
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        print("GOOGLE_API_KEY not found in .env")
        return

    print(f"Testing model: {model_name}")
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=model_name,
            contents=EXTRACTION_PROMPT,
            config={
                "temperature": 0.1,
                "max_output_tokens": 4096,
                "response_mime_type": "application/json",
            },
        )
        print(f"Response from {model_name}:")
        print(response.text)
    except Exception as e:
        print(f"Failed with {model_name}: {e}")

if __name__ == "__main__":
    asyncio.run(test_extraction("gemini-2.5-flash"))
    asyncio.run(test_extraction("gemini-2.0-flash"))
