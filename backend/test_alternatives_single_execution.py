"""
Regression tests for the confirmed V1 acceptance-audit bug: every
/analyze request executed find_alternatives() twice (once from
routes/analyze.py, once independently inside
insights_agent.generate_insights()), and the second, route-owned
call's result was the only one ever used -- the first call's
result was computed and then silently discarded. Confirmed live
across 19 real products as exactly 38 calls / 19 requests.

Fix: generate_insights() no longer computes its own alternatives.
It takes them as a required parameter, and routes/analyze.py
computes them exactly once and passes that same value into both
generate_insights() and the final response.
"""

import app.agents.insights_agent as insights_agent
import app.routes.analyze as analyze_route

from app.schemas.product import Product, ProductRequest, Specification


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


def _fake_product():
    return Product(
        title="Test Phone 5G",
        brand="TestBrand",
        price="₹19,999",
        rating=4.2,
        reviews=100,
        availability="In stock",
        specifications=[
            Specification(name="Operating System", value="Android 14"),
            Specification(name="Ram", value="8 GB"),
            Specification(name="Cellular", value="5G"),
        ],
        review_texts=[],
    )


SENTINEL_ALTERNATIVES = [
    {
        "name": "Sentinel Alternative Phone",
        "price": "₹18,999",
        "url": "https://www.amazon.in/dp/SENTINEL0001",
        "availability": "In stock",
        "verified": True,
        "reason": "test sentinel, not a real product",
    }
]


# ================================================================
# 1. Structural proof: insights_agent no longer imports or calls
# find_alternatives at all -- the only remaining call site is the
# route. This can't regress back to a silent second call.
# ================================================================

check(
    "insights_agent.py no longer imports find_alternatives",
    not hasattr(insights_agent, "find_alternatives"),
)

import inspect

check(
    "generate_insights() requires an `alternatives` parameter "
    "(the caller must supply an already-computed value)",
    "alternatives" in inspect.signature(insights_agent.generate_insights).parameters,
)


# ================================================================
# 2. generate_insights() propagates the passed-in alternatives
# into its own return value rather than computing/discarding its
# own -- tested directly, via the fast, network-free fallback
# path (Gemini client forced to None), so this doesn't depend on
# real Gemini/RAG availability.
# ================================================================

_original_client = insights_agent.client
_original_retrieve_context = insights_agent.retrieve_context

insights_agent.client = None
insights_agent.retrieve_context = lambda query, top_k=3: (_ for _ in ()).throw(
    AssertionError("retrieve_context should not be reached when client is None")
)

try:
    product = _fake_product()
    analysis = {"score": 55, "recommendation": "AVOID", "reasons": [], "summary": ""}

    result = insights_agent.generate_insights(
        product,
        product.specifications,
        analysis,
        "smartphone",
        SENTINEL_ALTERNATIVES,
    )

    check(
        "generate_insights() propagates the exact passed-in alternatives "
        "into its own return value, rather than discarding it",
        result["alternatives"] == SENTINEL_ALTERNATIVES,
    )

    empty_result = insights_agent.generate_insights(
        product,
        product.specifications,
        analysis,
        "smartphone",
        [],
    )

    check(
        "an empty alternatives list passed in stays empty in the output "
        "(never padded/fabricated)",
        empty_result["alternatives"] == [],
    )

finally:
    insights_agent.client = _original_client
    insights_agent.retrieve_context = _original_retrieve_context


# ================================================================
# 3. Route-level: find_alternatives() is called exactly once per
# /analyze request, and its result is the one that actually
# reaches the final response (not silently dropped).
# ================================================================

_original_find_alternatives = analyze_route.find_alternatives
_original_extract_product = analyze_route.extract_product

call_count = {"n": 0}
received_args = []


def _fake_find_alternatives(product, specs):
    call_count["n"] += 1
    received_args.append((product, specs))
    return {"alternatives": SENTINEL_ALTERNATIVES}


analyze_route.find_alternatives = _fake_find_alternatives
analyze_route.extract_product = lambda url: _fake_product()

# Force the fast, network-free fallback path inside generate_insights
# too, so this test doesn't depend on real Gemini/RAG availability.
insights_agent.client = None
insights_agent.retrieve_context = lambda query, top_k=3: []

try:
    request = ProductRequest(url="https://www.amazon.in/dp/TESTPRODUCT01")
    response = analyze_route._analyze(request)
finally:
    analyze_route.find_alternatives = _original_find_alternatives
    analyze_route.extract_product = _original_extract_product
    insights_agent.client = _original_client
    insights_agent.retrieve_context = _original_retrieve_context

check(
    "find_alternatives() is called exactly once per /analyze request "
    "(was confirmed as exactly 2 before this fix)",
    call_count["n"] == 1,
)
check(
    "the single call's result is propagated to the final response's "
    "'alternatives' field, not discarded",
    response["alternatives"] == SENTINEL_ALTERNATIVES,
)
check(
    "find_alternatives() is called with the real extracted product and specs",
    received_args[0][0].title == "Test Phone 5G",
)

print()
print("All single-execution / propagation checks passed.")
