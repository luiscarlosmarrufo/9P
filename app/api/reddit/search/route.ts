import { NextRequest, NextResponse } from "next/server";
import { REDDIT_USER_AGENT } from "@/lib/constants";
import {
  RedditSearchRequest,
  RedditPost,
  RedditAPIPost,
  RedditAPIResponse,
  RedditAccessTokenResponse,
} from "@/types/reddit";

async function getRedditAccessToken(
  clientId: string,
  clientSecret: string
): Promise<string> {
  const authString = Buffer.from(`${clientId}:${clientSecret}`).toString("base64");

  const response = await fetch("https://www.reddit.com/api/v1/access_token", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Authorization: `Basic ${authString}`,
      "User-Agent": REDDIT_USER_AGENT,
    },
    body: "grant_type=client_credentials",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Failed to get access token: ${error.error || "Unknown error"}`);
  }

  const data: RedditAccessTokenResponse = await response.json();
  return data.access_token;
}

async function searchRedditPosts(
  accessToken: string,
  brandName: string,
  startDate: Date,
  endDate: Date,
  after: string | null = null
): Promise<{ posts: RedditPost[]; nextAfter: string | null }> {
  const searchQuery = encodeURIComponent(brandName);
  let url = `https://oauth.reddit.com/search?q=${searchQuery}&sort=relevance&limit=100&type=link`;

  if (after) {
    url += `&after=${after}`;
  }

  console.log("Searching Reddit with URL:", url);

  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "User-Agent": REDDIT_USER_AGENT,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Reddit search failed: ${response.status} - ${error}`);
  }

  const data: RedditAPIResponse = await response.json();

  // Filter posts by date range and transform to our format
  const posts: RedditPost[] = data.data.children
    .map((item) => {
      const post = item.data;
      const postDate = new Date(post.created_utc * 1000);

      // Filter by date range
      if (postDate < startDate || postDate > endDate) {
        return null;
      }

      // Combine title and selftext
      const text = post.selftext
        ? `${post.title}\n\n${post.selftext}`
        : post.title;

      return {
        id: post.id,
        text: text,
        author: post.author,
        subreddit: post.subreddit,
        engagement: post.score,
        timestamp: postDate.toISOString(),
        url: `https://reddit.com${post.permalink}`,
        source: "reddit" as const,
      };
    })
    .filter((post): post is RedditPost => post !== null);

  return {
    posts,
    nextAfter: data.data.after,
  };
}

export async function POST(request: NextRequest) {
  try {
    const body: RedditSearchRequest = await request.json();

    // Validate required fields
    if (!body.brandName || !body.startDate || !body.endDate) {
      return NextResponse.json(
        { success: false, error: "Missing required fields: brandName, startDate, endDate" },
        { status: 400 }
      );
    }

    if (!body.clientId || !body.clientSecret) {
      return NextResponse.json(
        { success: false, error: "Reddit credentials are required" },
        { status: 401 }
      );
    }

    console.log(`Searching Reddit for brand: ${body.brandName}`);
    console.log(`Date range: ${body.startDate} to ${body.endDate}`);

    const startDate = new Date(body.startDate);
    const endDate = new Date(body.endDate);

    // Get Reddit access token
    let accessToken: string;
    try {
      accessToken = await getRedditAccessToken(body.clientId, body.clientSecret);
      console.log("Successfully obtained Reddit access token");
    } catch (error) {
      console.error("Failed to get Reddit access token:", error);
      return NextResponse.json(
        {
          success: false,
          error: "Invalid Reddit credentials",
          details: error instanceof Error ? error.message : "Unknown error",
        },
        { status: 401 }
      );
    }

    // Collect posts with pagination (up to 1500 posts max)
    const allPosts: RedditPost[] = [];
    let after: string | null = null;
    let requestCount = 0;
    const maxRequests = 15; // 15 requests * 100 posts = 1500 posts max

    while (requestCount < maxRequests) {
      try {
        const { posts, nextAfter } = await searchRedditPosts(
          accessToken,
          body.brandName,
          startDate,
          endDate,
          after
        );

        console.log(`Request ${requestCount + 1}: Found ${posts.length} posts`);

        allPosts.push(...posts);

        // No more posts available
        if (!nextAfter || posts.length === 0) {
          console.log("No more posts available");
          break;
        }

        after = nextAfter;
        requestCount++;

        // Rate limiting: Wait 1 second between requests (60 requests per minute)
        if (requestCount < maxRequests && nextAfter) {
          await new Promise((resolve) => setTimeout(resolve, 1000));
        }
      } catch (error) {
        console.error(`Error on request ${requestCount + 1}:`, error);

        // If we have some posts already, return them
        if (allPosts.length > 0) {
          console.log(`Returning ${allPosts.length} posts collected before error`);
          break;
        }

        // Check for rate limiting
        if (error instanceof Error && error.message.includes("429")) {
          return NextResponse.json(
            {
              success: false,
              error: "Reddit rate limit exceeded. Please try again in a few minutes.",
            },
            { status: 429 }
          );
        }

        throw error;
      }
    }

    console.log(`Total posts collected: ${allPosts.length}`);

    return NextResponse.json({
      success: true,
      posts: allPosts,
      total: allPosts.length,
    });
  } catch (error) {
    console.error("Error searching Reddit:", error);

    let errorMessage = "Failed to search Reddit posts";
    let statusCode = 500;

    if (error instanceof Error) {
      errorMessage = error.message;

      // Check for specific error types
      if (error.message.includes("credentials") || error.message.includes("401")) {
        statusCode = 401;
      } else if (error.message.includes("429") || error.message.includes("rate limit")) {
        statusCode = 429;
      }
    }

    return NextResponse.json(
      {
        success: false,
        error: errorMessage,
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: statusCode }
    );
  }
}
