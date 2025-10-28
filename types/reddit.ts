export interface RedditSearchRequest {
  brandName: string;
  startDate: string;
  endDate: string;
  clientId: string;
  clientSecret: string;
}

export interface RedditPost {
  id: string;
  text: string;
  author: string;
  subreddit: string;
  engagement: number;
  timestamp: string;
  url: string;
  source: "reddit";
}

export interface RedditSearchResponse {
  success: boolean;
  posts: RedditPost[];
  total: number;
  error?: string;
  details?: string;
}

export interface RedditAPIPost {
  data: {
    id: string;
    title: string;
    selftext: string;
    author: string;
    subreddit: string;
    score: number;
    created_utc: number;
    permalink: string;
  };
}

export interface RedditAPIResponse {
  data: {
    children: RedditAPIPost[];
    after: string | null;
    before: string | null;
  };
}

export interface RedditAccessTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  scope: string;
}
