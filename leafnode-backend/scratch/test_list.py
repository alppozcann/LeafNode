import asyncio
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

async def test_list():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    try:
        models = await client.aio.models.list()
        print(f"Found {len(list(models))} models.")
        for m in models:
            name = m.name.split("/")[-1]
            print(f"  - {name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_list())
