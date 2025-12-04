export interface ClassificationRequest {
  posts: PostToClassify[];
  anthropicApiKey: string;
}

export interface PostToClassify {
  id: string;
  text: string;
  author?: string;
  subreddit?: string;
  engagement?: number;
  timestamp?: string;
  url?: string;
  source: string;
}

export interface PostClassification {
  post_id: string;
  categories: string[];
  sentiment: "positive" | "neutral" | "negative";
  confidence: number;
  reasoning: string;
}

export interface ClassificationResponse {
  success: boolean;
  classifications: PostClassification[];
  processed: number;
  cost_estimate: string;
  error?: string;
}

export interface ClaudeClassificationResult {
  post_index: number;
  categories: string[];
  sentiment: "positive" | "neutral" | "negative";
  confidence: number;
  reasoning: string;
}

export interface ClaudeClassificationResponse {
  classifications: ClaudeClassificationResult[];
}

export const NINE_PS_CATEGORIES = [
  "Product",
  "Price",
  "Place",
  "Publicity",
  "Production",
  "Pre-Consumption",
  "Disposal",
  "Purpose Drive",
  "People",
] as const;
