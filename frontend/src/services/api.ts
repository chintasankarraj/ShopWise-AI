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
  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      url,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to analyze product");
  }

  const data: ProductAnalysis = await response.json();

  return data;
}