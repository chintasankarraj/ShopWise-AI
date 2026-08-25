import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)


def analyze_product(
    product,
    specs,
    analysis,
    review_report,
    price_report,
):

    prompt = f"""
You are ShopWise AI.

You are the FINAL DECISION AGENT.

Use ALL available information.

========================
PRODUCT
========================

Title:
{product.title}

Brand:
{product.brand}

Price:
{product.price}

========================
SPECIFICATIONS
========================

{specs}

========================
RULE-BASED ANALYSIS
========================

{analysis}

========================
CUSTOMER REVIEW ANALYSIS
========================

{review_report}

========================
PRICE ANALYSIS
========================

{price_report}

========================

Now generate a professional buying report.

Include:

1. Overall Score (/100)

2. Final Recommendation

3. Strengths

4. Weaknesses

5. Who should buy it?

6. Is it worth the money?

7. Final Verdict

"""