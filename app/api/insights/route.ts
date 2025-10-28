import { NextRequest, NextResponse } from "next/server";
import { ANTHROPIC_MODEL, ANTHROPIC_API_VERSION } from "@/lib/constants";

interface InsightRequest {
  analysisId: string;
  brandName: string;
  stats: {
    totalPosts: number;
    classified: number;
    sentimentBreakdown: {
      positive: number;
      neutral: number;
      negative: number;
    };
    categoryBreakdown: Record<string, number>;
    timeRange: string;
  };
  samplePosts: Array<{
    text: string;
    categories: string[];
    sentiment: string;
    engagement: number;
  }>;
  anthropicApiKey: string;
}

export async function POST(request: NextRequest) {
  console.log("=== INSIGHTS API CALLED ===");

  try {
    const body: InsightRequest = await request.json();

    console.log("Generating insights for:", body.brandName);
    console.log("Analysis ID:", body.analysisId);
    console.log("Total posts:", body.stats.totalPosts);

    if (!body.anthropicApiKey) {
      return NextResponse.json(
        { success: false, error: "Anthropic API key is required" },
        { status: 401 }
      );
    }

    // Calculate percentages
    const total = body.stats.totalPosts;
    const posPercentage = total > 0 ? Math.round((body.stats.sentimentBreakdown.positive / total) * 100) : 0;
    const neuPercentage = total > 0 ? Math.round((body.stats.sentimentBreakdown.neutral / total) * 100) : 0;
    const negPercentage = total > 0 ? Math.round((body.stats.sentimentBreakdown.negative / total) * 100) : 0;

    // Get top 3 categories
    const topCategories = Object.entries(body.stats.categoryBreakdown)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3)
      .map(([cat, count]) => `${cat} (${count} posts)`)
      .join(", ");

    // Format sample posts
    const samplePostsText = body.samplePosts
      .slice(0, 10)
      .map((post, idx) => {
        return `Post ${idx + 1} (${post.engagement} engagement, ${post.sentiment}):
Categories: ${post.categories.join(", ")}
Text: ${post.text.substring(0, 300)}...`;
      })
      .join("\n\n");

    const prompt = `You are a senior brand strategy consultant analyzing social media sentiment for ${body.brandName}.

ANALYSIS SUMMARY:
- Time Period: ${body.stats.timeRange}
- Total Posts Analyzed: ${body.stats.totalPosts}
- Classified: ${body.stats.classified}
- Sentiment: ${posPercentage}% positive, ${neuPercentage}% neutral, ${negPercentage}% negative
- Top Categories: ${topCategories}

SAMPLE HIGH-ENGAGEMENT POSTS:
${samplePostsText}

TASK: Provide strategic recommendations in this exact JSON format (respond with ONLY the JSON, no other text):
{
  "executiveSummary": "2-3 sentence overview of brand health",
  "keyFindings": [
    {
      "title": "Finding name (e.g., Price Perception Crisis)",
      "severity": "critical" | "warning" | "opportunity",
      "description": "What the data shows",
      "impact": "Why it matters for the business",
      "evidence": "Specific data points"
    }
  ],
  "recommendations": [
    {
      "priority": "high" | "medium" | "low",
      "category": "Product" | "Marketing" | "Customer Service" | etc,
      "action": "Specific actionable recommendation",
      "rationale": "Why this will help",
      "expectedOutcome": "What success looks like"
    }
  ],
  "opportunities": [
    {
      "area": "Area name",
      "description": "What the opportunity is",
      "suggestion": "How to capitalize on it"
    }
  ]
}

Focus on:
- Actionable recommendations (not just observations)
- Prioritize by business impact
- Use specific data from the analysis
- Identify both risks and opportunities
- Keep recommendations concrete and measurable
- Generate 3-5 key findings, 4-6 recommendations, and 2-4 opportunities`;

    console.log("Sending request to Anthropic API for insights...");

    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "x-api-key": body.anthropicApiKey,
        "anthropic-version": ANTHROPIC_API_VERSION,
        "content-type": "application/json",
      },
      body: JSON.stringify({
        model: ANTHROPIC_MODEL,
        max_tokens: 4096,
        messages: [
          {
            role: "user",
            content: prompt,
          },
        ],
      }),
    });

    console.log(`Anthropic API response status: ${response.status}`);

    if (!response.ok) {
      const error = await response.json();
      console.error("Anthropic API error:", error);
      throw new Error(
        `Claude API error: ${error.error?.message || response.statusText}`
      );
    }

    const data = await response.json();
    const content = data.content[0].text;

    console.log("Raw content length:", content.length);

    const insights = JSON.parse(content);

    console.log("✓ Successfully generated insights");
    console.log("Key findings:", insights.keyFindings?.length || 0);
    console.log("Recommendations:", insights.recommendations?.length || 0);
    console.log("Opportunities:", insights.opportunities?.length || 0);

    // Calculate token usage for cost estimation
    const inputTokens = data.usage?.input_tokens || 0;
    const outputTokens = data.usage?.output_tokens || 0;
    const inputCost = (inputTokens / 1_000_000) * 0.8;
    const outputCost = (outputTokens / 1_000_000) * 4.0;
    const totalCost = inputCost + outputCost;

    return NextResponse.json({
      success: true,
      insights,
      cost_estimate: `$${totalCost.toFixed(4)}`,
      tokens: {
        input: inputTokens,
        output: outputTokens,
      },
    });
  } catch (error) {
    console.error("=== INSIGHTS GENERATION ERROR ===");
    console.error("Error generating insights:", error);

    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Failed to generate insights",
      },
      { status: 500 }
    );
  }
}
