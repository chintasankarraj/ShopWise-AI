"""
Regression tests for the production hang fix: every Gemini SDK
client must be constructed with an explicit, bounded HTTP
timeout (the SDK's default is unbounded -- httpx timeout=None --
which was empirically proven, via a controlled local
reproduction against an unresponsive socket, to hang forever
with zero client-side protection). Also covers the shorter
timeout override used for best-effort alternatives verification.
"""

import app.agents.insights_agent as insights_agent
import app.agents.alternative_agent as alternative_agent
import app.rag.embeddings as embeddings
import app.services.scraperapi_product_provider as scraperapi_product_provider


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    assert condition, label


def configured_timeout_ms(client):
    return client._api_client._http_options.timeout


# ================================================================
# Every Gemini client has an explicit, bounded timeout configured
# ================================================================

for label, client, expected_ms in [
    ("insights_agent.client", insights_agent.client, insights_agent._GEMINI_TIMEOUT_MS),
    ("alternative_agent.client", alternative_agent.client, alternative_agent._GEMINI_TIMEOUT_MS),
    ("embeddings.client", embeddings.client, embeddings._GEMINI_EMBEDDING_TIMEOUT_MS),
]:
    if client is None:
        print(f"[SKIP] {label} is None (no GEMINI_API_KEY configured in this environment)")
        continue

    timeout_ms = configured_timeout_ms(client)

    check(
        f"{label} has an explicit HTTP timeout configured (not None/unbounded)",
        timeout_ms is not None,
    )
    check(
        f"{label}'s configured timeout is bounded and positive ({timeout_ms}ms)",
        isinstance(timeout_ms, (int, float)) and timeout_ms > 0,
    )
    check(
        f"{label}'s configured timeout matches its module constant ({expected_ms}ms)",
        timeout_ms == expected_ms,
    )
    check(
        f"{label}'s timeout is a sane production value (between 5s and 60s)",
        5_000 <= timeout_ms <= 60_000,
    )


# ================================================================
# fetch_product_from_scraperapi(): timeout parameter behavior
# ================================================================

captured = {}


def fake_get(url, params=None, timeout=None):
    captured["timeout"] = timeout

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"name": "Test Product"}

    return FakeResponse()


import os

os.environ.setdefault("SCRAPERAPI_KEY", "test-key-for-timeout-test")
scraperapi_product_provider.requests.get = fake_get

scraperapi_product_provider.fetch_product_from_scraperapi(
    "https://www.amazon.in/dp/B0DGJ7TGDR"
)
check(
    "fetch_product_from_scraperapi() defaults to the existing 60s timeout "
    "when no override is given (backward compatible for the primary "
    "extraction path)",
    captured["timeout"] == 60,
)

scraperapi_product_provider.fetch_product_from_scraperapi(
    "https://www.amazon.in/dp/B0DGJ7TGDR",
    timeout=20,
)
check(
    "fetch_product_from_scraperapi() honors an explicit shorter timeout override",
    captured["timeout"] == 20,
)


# ================================================================
# Alternative verification uses the shorter, bounded timeout --
# never the primary extraction's full 60s -- for each candidate.
# ================================================================

verify_calls = []


def fake_fetch_for_verify(url, timeout=60):
    verify_calls.append(timeout)

    class FakeVerifiedProduct:
        price = "₹19,999"
        availability = "In stock"

    return FakeVerifiedProduct()


alternative_agent.fetch_product_from_scraperapi = fake_fetch_for_verify

alternative_agent._verify_amazon_availability(
    "https://www.amazon.in/dp/B0DSKMV3ZC"
)

check(
    "alternative verification uses the shorter "
    f"_ALTERNATIVE_VERIFICATION_TIMEOUT_SECONDS "
    f"({alternative_agent._ALTERNATIVE_VERIFICATION_TIMEOUT_SECONDS}s), "
    "not the primary extraction's 60s default",
    verify_calls == [alternative_agent._ALTERNATIVE_VERIFICATION_TIMEOUT_SECONDS],
)
check(
    "the verification timeout is meaningfully shorter than the primary "
    "extraction timeout, bounding worst-case sequential-verification latency",
    alternative_agent._ALTERNATIVE_VERIFICATION_TIMEOUT_SECONDS < 60,
)

print()
print("All network timeout checks passed.")
