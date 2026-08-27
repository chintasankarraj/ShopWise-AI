export interface Specification {
  name: string;
  value: string;
}

export interface Product {
  title: string;
  brand: string | null;
  price: string | null;
  rating: number | null;
  reviews: number | null;
  image: string | null;
  availability: string | null;
  category?: string;
  specifications: Specification[];
}

export interface Analysis {
  score: number;
  recommendation: string;
  reasons: string[];
  summary: string;
}

export interface ReviewReport {
  overall_sentiment: string;
  top_pros: string[];
  top_cons: string[];
  common_complaints: string[];
  best_for: string;
}

export interface PriceReport {
  current_value: string;
  expected_sale_price: string;
  buy_advice: string;
  reason: string;
}

export interface AIReport {
  overall_score: number;
  recommendation: string;
  summary: string;
  pros: string[];
  cons: string[];
}

export interface Alternative {
  name: string;
  price: string;
  reason: string;
  url: string;
  availability?: string;
  verified?: boolean;
}

export interface ProductAnalysis {
  product: Product;
  analysis: Analysis;
  review_report: ReviewReport;
  price_report: PriceReport;
  alternatives: Alternative[];
  ai_report: AIReport;
}