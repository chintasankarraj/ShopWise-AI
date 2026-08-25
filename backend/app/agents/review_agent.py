import os
import json

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def analyze_reviews(product):

    prompt = f"""
You are ShopWise AI.

Analyze customer reviews for this product.

Title:
{product.title}

Return ONLY valid JSON.

Do not explain anything.
Do not use markdown.
Do not wrap the response inside ```.

Return exactly:

{{
    "sentiment": "",
    "pros": [
        "",
        "",
        ""
    ],
    "cons": [
        "",
        "",
        ""
    ],
    "complaints": [
        "",
        ""
    ],
    "best_for": ""
}}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    return json.loads(text)