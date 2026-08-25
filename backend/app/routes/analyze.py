import traceback

import requests
from fastapi import APIRouter, HTTPException

from app.schemas.product import ProductRequest
from app.services.product_extractor import extract_product
from app.services.category_detector import detect_category
from app.agents.recommendation_agent import recommend
from app.agents.insights_agent import generate_insights
from app.agents.alternative_agent import find_alternatives


router = APIRouter()


@router.post("/analyze")
def analyze(request: ProductRequest):

    try:
        return _analyze(request)

    # ==================================================
    # The product page could not be fetched (blocked,
    # timed out, DNS failure, etc). Distinct from a
    # generic 500 so the frontend/dev can tell "we
    # couldn't reach the retailer" apart from "our code
    # broke".
    # ==================================================

    except requests.exceptions.RequestException as error:

        traceback.print_exc()

        raise HTTPException(
            status_code=502,
            detail=(
                "Could not fetch the product page. The "
                "retailer may be blocking automated "
                "requests, or the URL may be unreachable. "
                f"Details: {error}"
            ),
        )

    # ==================================================
    # Anything else (parsing errors, unexpected
    # response shapes, etc). The real exception is kept
    # in the response detail on purpose -- this is
    # pre-launch and we want failures to be diagnosable
    # from the frontend without needing server logs.
    # ==================================================

    except Exception as error:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze product: {error}",
        )


def _analyze(request: ProductRequest):

    # ==================================================
    # 1. Extract product
    # ==================================================

    product = extract_product(request.url)

    # ==================================================
    # 2. Get specifications
    # ==================================================

    specs = product.specifications
    print("=" * 80)
    print("LIVE EXTRACTED SPECIFICATIONS")
    print("=" * 80)

    for spec in specs:
        print(
            f"{spec.name}: {spec.value}"
        )

    print("=" * 80)

    # ==================================================
    # 3. Detect category
    # ==================================================

    category = detect_category(
        product.title,
        specs
    )

    # ==================================================
    # 4. Generate recommendation
    # ==================================================

    analysis = recommend(
        specs,
        category
    )
    print("=" * 80)
    print("LIVE RECOMMENDATION DEBUG")
    print("CATEGORY:", category)
    print("SCORE:", analysis.get("score"))
    print("RECOMMENDATION:", analysis.get("recommendation"))
    print("REASONS:")

    for reason in analysis.get("reasons", []):
        print("-", reason)

    print("=" * 80)

    # ==================================================
    # 5. Generate AI insights
    # ==================================================

    insights = generate_insights(
        product,
        specs,
        analysis,
        category
    )

    # ==================================================
    # 5.1 Find better alternatives
    # ==================================================

    alternative_report = find_alternatives(
        product,
        specs
    )

    alternatives = alternative_report.get(
        "alternatives",
        []
    )

    # ==================================================
    # 6. Final unified response
    # ==================================================

    return {

        "product": {

            "title": product.title,

            "brand": product.brand,

            "price": product.price,

            "rating": product.rating,

            "reviews": product.reviews,

            "image": product.image,

            "availability": product.availability,

            "category": category,

            "specifications": [
                {
                    "name": spec.name,
                    "value": spec.value,
                }
                for spec in product.specifications
            ],
        },

        "analysis": analysis,

        "review_report": insights.get(
            "review_report",
            {
                "overall_sentiment": "Not Available",
                "top_pros": [],
                "top_cons": [],
                "common_complaints": [],
                "best_for": "Not Available",
            }
        ),

        "price_report": insights.get(
            "price_report",
            {
                "current_value": (
                    product.price
                    if product.price
                    else "Not Available"
                ),
                "expected_sale_price": "Not Available",
                "buy_advice": analysis["recommendation"],
                "reason": (
                    "Historical price data is "
                    "not available."
                ),
            }
        ),

        "alternatives": alternatives,

        "ai_report": insights.get(
            "ai_report",
            {
                "overall_score": analysis["score"],
                "recommendation": analysis["recommendation"],
                "summary": analysis["summary"],
                "pros": analysis["reasons"],
                "cons": [],
            }
        ),
    }