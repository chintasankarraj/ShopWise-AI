from app.agents.specification_agent import extract_specs
from app.agents.recommendation_agent import recommend
from app.agents.review_agent import analyze_reviews
from app.agents.price_agent import analyze_price
from app.agents.alternative_agent import find_alternatives


def run_agents(product):

    # ========================================================
    # 1. Extract specifications
    # ========================================================

    specs = extract_specs(
        product.title
    )

    # ========================================================
    # 2. Generate baseline recommendation
    # ========================================================

    recommendation = recommend(
        specs
    )

    # ========================================================
    # 3. Analyze customer reviews
    # ========================================================

    review_report = analyze_reviews(
        product
    )

    # ========================================================
    # 4. Analyze price
    # ========================================================

    price_report = analyze_price(
        product
    )

    # ========================================================
    # 5. Find alternatives
    # ========================================================

    alternative_report = find_alternatives(
        product,
        specs
    )

    # ========================================================
    # 6. Return all agent results
    # ========================================================

    return {
        "product": product,

        "specifications": specs,

        "analysis": recommendation,

        "review_report": review_report,

        "price_report": price_report,

        "alternatives": alternative_report.get(
            "alternatives",
            []
        ),
    }