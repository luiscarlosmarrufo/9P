export interface AnalysisData {
  id: string;
  brand_name: string;
  date_range: string;
  start_date: string;
  end_date: string;
  total_posts: number;
  status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
}

export interface PostWithClassification {
  id: string;
  text: string;
  author: string;
  subreddit?: string;
  engagement: number;
  timestamp: string;
  url: string;
  source: string;
  categories: string[];
  sentiment: "positive" | "neutral" | "negative";
  confidence: number;
  reasoning: string;
}

export interface SentimentBreakdown {
  positive: number;
  neutral: number;
  negative: number;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface SentimentOverTime {
  date: string;
  score: number;
  count: number;
}
