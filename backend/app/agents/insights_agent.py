import json
import os

from app.agents.alternative_agent import find_alternatives
from app.rag.retriever import retrieve_context, format_context

from dotenv import load_dotenv
from google import genai

load_dotenv()


# ============================================================
# GEMINI CLIENT
# ============================================================

api_key = os.getenv("GEMINI_API_KEY")

client = None

if api_key:
    client = genai.Client(
        api_key=api_key
    )


# ============================================================
# AI INSIGHTS
# ============================================================

def generate_insights(
    product,
    specs,
    analysis,
    category
):
    """
    Generate AI-based product insights using:

    1. Product specifications
    2. Rule-based recommendation engine
    3. RAG-retrieved product knowledge
    4. Gemini reasoning

    RAG is used to provide relevant external
    knowledge before Gemini generates the report.

    Gemini must NOT invent:
    - customer reviews
    - historical prices
    - sale prices
    - product specifications
    - alternative products
    """

    # ========================================================
    # 1. SERIALIZE SPECIFICATIONS
    # ========================================================

    specification_data = []

    for spec in specs or []:

        if hasattr(spec, "model_dump"):

            specification_data.append(
                spec.model_dump()
            )

        elif isinstance(spec, dict):

            specification_data.append(
                spec
            )

        else:

            specification_data.append(
                {
                    "name": getattr(
                        spec,
                        "name",
                        ""
                    ),
                    "value": getattr(
                        spec,
                        "value",
                        ""
                    ),
                }
            )

    # ========================================================
    # 2. BUILD RAG QUERY
    # ========================================================

    rag_query = _build_rag_query(
        product,
        specification_data,
        category
    )

    print()
    print("=" * 80)
    print("SHOPWISE RAG")
    print("=" * 80)

    print("RAG QUERY:")
    print(rag_query)

    # ========================================================
    # 3. RETRIEVE KNOWLEDGE
    # ========================================================

    try:

        retrieved_context = retrieve_context(
            rag_query,
            top_k=3
        )

        rag_context = format_context(
            retrieved_context
        )

        print()
        print(
            f"Retrieved RAG chunks: "
            f"{len(retrieved_context)}"
        )

        for index, item in enumerate(
            retrieved_context,
            start=1
        ):

            print(
                f"\nRAG RESULT #{index}"
            )

            print(
                f"Source: {item['source']}"
            )

    except Exception as error:

        print()
        print(
            "RAG retrieval failed:",
            error
        )

        retrieved_context = []

        rag_context = (
            "No external knowledge was "
            "successfully retrieved."
        )

    print("=" * 80)

    # ========================================================
    # 4. GENERATE ALTERNATIVES
    # ========================================================

    try:

        alternative_result = find_alternatives(
            product,
            specs
        )

        alternatives = alternative_result.get(
            "alternatives",
            []
        )

    except Exception as error:

        print("=" * 80)

        print(
            "ALTERNATIVE AGENT ERROR:",
            error
        )

        print("=" * 80)

        alternatives = []

    # ========================================================
    # 5. GEMINI UNAVAILABLE
    # ========================================================

    if client is None:

        return _fallback_insights(
            product,
            analysis,
            alternatives
        )

    # ========================================================
    # 6. GEMINI PROMPT
    # ========================================================

    prompt = f"""
You are ShopWise AI, an expert product analysis assistant.

Your job is to analyze the product using:

1. Actual product information
2. Extracted specifications
3. The deterministic recommendation engine
4. Retrieved knowledge from the ShopWise knowledge base

IMPORTANT:

The retrieved knowledge is supporting context.

Do NOT treat the retrieved knowledge as if it were
specific product facts unless those facts are also
present in the PRODUCT or SPECIFICATIONS sections.

Do NOT invent information.

Do NOT invent:
- product specifications
- customer reviews
- historical prices
- sale prices
- availability
- product alternatives

You may make reasonable conclusions from the
provided specifications and retrieved general
knowledge.

============================================================
PRODUCT
============================================================

Title:
{product.title}

Brand:
{product.brand}

Category:
{category}

Current Price:
{product.price}

Rating:
{product.rating}

Review Count:
{product.reviews}

Availability:
{product.availability}

============================================================
SPECIFICATIONS
============================================================

{json.dumps(
    specification_data,
    indent=2,
    ensure_ascii=False
)}

============================================================
BASELINE RECOMMENDATION
============================================================

{json.dumps(
    analysis,
    indent=2,
    ensure_ascii=False
)}

============================================================
RETRIEVED KNOWLEDGE — RAG
============================================================

{rag_context}

============================================================
HOW TO USE THE RAG CONTEXT
============================================================

Use the retrieved knowledge to explain the meaning
and implications of the product specifications.

For example:

- If the product has a high refresh rate, explain
  what that generally means for smoothness.

- If the product uses LCD instead of AMOLED/OLED,
  explain the general display trade-off.

- If the product has a large battery, explain why
  battery capacity can be beneficial while noting
  that actual battery life depends on usage and
  efficiency.

- If the product has high RAM or storage, explain
  the practical benefit.

Do not claim that the retrieved knowledge proves
specific product performance.

============================================================
REVIEW REPORT
============================================================

Actual customer review text is NOT available.

Therefore return:

"overall_sentiment": "Not Available"

"top_pros": []

"top_cons": []

"common_complaints": []

"best_for": "Not Available"

Do not generate customer opinions from specifications.

============================================================
PRICE REPORT
============================================================

The current price is known.

Historical price data is NOT available.

Therefore:

"current_value":
use the actual current product price.

"expected_sale_price":
"Not Available"

"buy_advice":
must match the baseline recommendation.

Do not invent historical prices.

Do not invent expected sale prices.

============================================================
ALTERNATIVES
============================================================

Alternative products are generated separately
by the Alternative Agent.

Do NOT generate alternatives yourself.

Return:

"alternatives": []

The application will insert the actual
Alternative Agent results afterwards.

============================================================
AI REPORT
============================================================

The overall score MUST come from the
rule-based recommendation engine.

Use:

overall_score =
{analysis["score"]}

recommendation =
{analysis["recommendation"]}

The summary should explain the recommendation
using:

- actual specifications
- baseline recommendation
- relevant RAG knowledge

Pros and cons must be supported by the
available product information.

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

Do not use markdown.

Use exactly:

{{
    "review_report": {{
        "overall_sentiment": "Not Available",
        "top_pros": [],
        "top_cons": [],
        "common_complaints": [],
        "best_for": "Not Available"
    }},

    "price_report": {{
        "current_value": "",
        "expected_sale_price": "Not Available",
        "buy_advice": "",
        "reason": ""
    }},

    "alternatives": [],

    "ai_report": {{
        "overall_score": 0,
        "recommendation": "",
        "summary": "",
        "pros": [],
        "cons": []
    }}
}}
"""

    # ========================================================
    # 7. CALL GEMINI
    # ========================================================

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
        )

        text = response.text.strip()

        # ----------------------------------------------------
        # Remove markdown JSON fences
        # ----------------------------------------------------

        if text.startswith("```json"):

            text = text[7:]

        elif text.startswith("```"):

            text = text[3:]

        if text.endswith("```"):

            text = text[:-3]

        text = text.strip()

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        result = json.loads(
            text
        )

        # ====================================================
        # SCORE CONTROLLED BY RULE ENGINE
        # ====================================================

        result["ai_report"]["overall_score"] = (
            analysis["score"]
        )

        result["ai_report"]["recommendation"] = (
            analysis["recommendation"]
        )

        # ====================================================
        # INSERT ALTERNATIVES
        # ====================================================

        result["alternatives"] = alternatives

        # ====================================================
        # DEBUG
        # ====================================================

        print()
        print("=" * 80)
        print("GEMINI + RAG INSIGHTS")
        print("=" * 80)

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False
            )
        )

        print("=" * 80)

        return result

    # ========================================================
    # GEMINI FAILURE
    # ========================================================

    except Exception as error:

        print("=" * 80)

        print(
            "GEMINI ERROR:",
            error
        )

        print(
            "Using deterministic fallback."
        )

        print("=" * 80)

        return _fallback_insights(
            product,
            analysis,
            alternatives
        )


# ============================================================
# BUILD RAG QUERY
# ============================================================

def _build_rag_query(
    product,
    specifications,
    category
):
    """
    Build a focused semantic query for RAG.

    Only important decision-making specifications
    are included so the embedding search focuses
    on useful product knowledge.
    """

    important_keywords = {
        "processor",
        "cpu",
        "ram",
        "storage",
        "display",
        "refresh rate",
        "battery",
        "charging",
        "camera",
        "cellular",
        "5g",
        "water resistance",
        "weight",
    }

    important_specs = []

    for spec in specifications:

        name = str(
            spec.get(
                "name",
                ""
            )
        ).strip()

        value = str(
            spec.get(
                "value",
                ""
            )
        ).strip()

        if not name or not value:
            continue

        normalized_name = name.lower()

        if any(
            keyword in normalized_name
            for keyword in important_keywords
        ):

            important_specs.append(
                f"{name}: {value}"
            )

    return (
        f"{category} product evaluation. "
        f"Important buying factors: "
        f"{', '.join(important_specs)}"
    )

# ============================================================
# FALLBACK
# ============================================================

def _fallback_insights(
    product,
    analysis,
    alternatives
):

    recommendation = analysis.get(
        "recommendation",
        "CONSIDER"
    )

    score = analysis.get(
        "score",
        0
    )

    summary = analysis.get(
        "summary",
        "Product analysis is based on available specifications."
    )

    return {

        "review_report": {

            "overall_sentiment":
                "Not Available",

            "top_pros":
                [],

            "top_cons":
                [],

            "common_complaints":
                [],

            "best_for":
                "Not Available",
        },

        "price_report": {

            "current_value": (
                product.price
                if product.price
                else "Not Available"
            ),

            "expected_sale_price":
                "Not Available",

            "buy_advice":
                recommendation,

            "reason": (
                "Historical price data is not available. "
                "The recommendation is based on the "
                "available product specifications."
            ),
        },

        "alternatives":
            alternatives,

        "ai_report": {

            "overall_score":
                score,

            "recommendation":
                recommendation,

            "summary":
                summary,

            "pros":
                analysis.get(
                    "reasons",
                    []
                ),

            "cons":
                [],
        },
    }