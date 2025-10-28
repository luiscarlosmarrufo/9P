// Anthropic API Configuration
export const ANTHROPIC_MODEL = "claude-3-5-haiku-20241022";
export const ANTHROPIC_API_VERSION = "2023-06-01";

// Reddit API Configuration
export const REDDIT_USER_AGENT = "9P Social Analytics/1.0";

// Analysis Configuration
export const TIME_RANGES = {
  "7": { days: 7, label: "7 days" },
  "30": { days: 30, label: "30 days" },
  "90": { days: 90, label: "90 days" },
} as const;

// 9Ps Marketing Framework Categories
export const NINE_PS_CATEGORIES = [
  "Product",
  "Price",
  "Place",
  "Promotion",
  "People",
  "Process",
  "Physical Evidence",
  "Performance",
  "Purpose",
] as const;

// Sentiment Types
export const SENTIMENT_TYPES = ["positive", "neutral", "negative"] as const;
