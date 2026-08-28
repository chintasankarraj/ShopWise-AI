import { ProductAnalysis } from "@/types/product";

// Set NEXT_PUBLIC_API_URL in the environment for deployed builds
// (e.g. https://api.example.com). Falls back to localhost for
// local development so `/analyze` behavior is unchanged there.
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const API_URL = `${API_BASE_URL}/analyze`;

export async function analyzeProduct(
  url: string
): Promise<ProductAnalysis> {
  let response: Response;

  try {
    response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        url,
      }),
    });
  } catch {
    throw new Error(
      "Could not reach the ShopWise server. Check your connection and try again."
    );
  }

  if (!response.ok) {
    let detail = "";

    try {
      const errorBody = await response.json();

      if (typeof errorBody?.detail === "string") {
        // Application-level errors (HTTPException) — a plain string.
        detail = errorBody.detail;
      } else if (Array.isArray(errorBody?.detail)) {
        // Request-validation errors (422) — an array of { msg } objects.
        detail = errorBody.detail
          .map((item: { msg?: string }) =>
            typeof item?.msg === "string"
              ? item.msg.replace(/^Value error,\s*/, "")
              : ""
          )
          .filter(Boolean)
          .join(" ");
      }
    } catch {
      // Response body wasn't JSON — fall back to a generic message below.
    }

    throw new Error(
      detail || "Failed to analyze the product. Please try again."
    );
  }

  try {
    return (await response.json()) as ProductAnalysis;
  } catch {
    throw new Error(
      "Received an unexpected response from the server. Please try again."
    );
  }
}