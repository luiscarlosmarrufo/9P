import { NextRequest, NextResponse } from "next/server";
import { ANTHROPIC_MODEL, ANTHROPIC_API_VERSION } from "@/lib/constants";

const BATCH_SIZE = 20;

interface PostToClassify {
  id: string; // Supabase UUID
  text: string;
  post_id?: string; // Original Reddit ID (optional)
}

interface PostClassification {
  post_id: string; // Supabase UUID
  categories: string[];
  sentiment: "positive" | "neutral" | "negative";
  confidence: number;
  reasoning: string;
}

const NINE_PS_CATEGORIES = [
  "Product",
  "Place",
  "Price",
  "Publicity",
  "Post-consumption",
  "Purpose",
  "Partnerships",
  "People",
  "Planet",
];

async function classifyBatch(
  posts: Array<{ id: string; text: string; index: number }>,
  brandName: string,
  apiKey: string
): Promise<PostClassification[]> {
  console.log(`\n=== CLASSIFYING BATCH ===`);
  console.log(`Batch size: ${posts.length} posts`);
  console.log(`Brand name: ${brandName}`);
  console.log(`API key length: ${apiKey?.length || 0}`);
  console.log(`Post IDs in batch: ${posts.map(p => p.id.substring(0, 8)).join(", ")}...`);

  const postsText = posts
    .map((p) => `Post ${p.index}:\n${p.text.substring(0, 500)}`)
    .join("\n\n");

  console.log(`Posts text length: ${postsText.length} characters`);

  const prompt = `You are a marketing analyst. Classify these social media posts about ${brandName} into the 9Ps of marketing and determine sentiment.

9Ps categories:
- Product: Features, quality, design, functionality
- Place: Distribution, availability, location
- Price: Cost, value, pricing strategy
- Publicity: Advertising, PR, brand awareness
- Post-consumption: Customer service, support, returns
- Purpose: Brand mission, values, social responsibility
- Partnerships: Collaborations, sponsorships
- People: Employees, leadership, company culture
- Planet: Sustainability, environmental impact

For each post, identify ALL relevant categories (can be multiple), sentiment (positive/neutral/negative), confidence score (0-1), and brief reasoning (1 sentence).

Posts:
${postsText}

Respond with ONLY a JSON object in this exact format (no other text):
{
  "classifications": [
    {
      "post_index": 0,
      "categories": ["Product", "Price"],
      "sentiment": "positive",
      "confidence": 0.85,
      "reasoning": "Brief explanation here"
    }
  ]
}`;

  console.log("Sending request to Anthropic API...");
  console.log(`Using model: ${ANTHROPIC_MODEL}`);
  console.log(`Max tokens: 4096`);

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": apiKey,
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

  console.log(`Anthropic API response status: ${response.status} ${response.statusText}`);

  if (!response.ok) {
    const error = await response.json();
    console.error("ERROR: Anthropic API error:", JSON.stringify(error, null, 2));
    throw new Error(
      `Claude API error: ${error.error?.message || response.statusText}`
    );
  }

  const data = await response.json();
  console.log("✓ Anthropic API response received successfully");
  console.log(`Response content type: ${data.content?.[0]?.type}`);
  console.log(`Response has content: ${!!data.content?.[0]?.text}`);

  const content = data.content[0].text;
  console.log(`Content length: ${content?.length || 0} characters`);

  const parsed = JSON.parse(content);
  console.log(`✓ Parsed ${parsed.classifications?.length || 0} classifications from Claude`);

  if (parsed.classifications && parsed.classifications.length > 0) {
    console.log("Sample classification:", JSON.stringify(parsed.classifications[0], null, 2));
  }

  // Map back to Supabase post UUIDs
  console.log("Mapping classifications to Supabase post IDs...");
  const classifications: PostClassification[] = parsed.classifications.map((c: any) => {
    const post = posts.find((p) => p.index === c.post_index);
    if (!post) {
      console.error(`ERROR: Could not find post for index ${c.post_index}`);
      console.error(`Available post indices: ${posts.map(p => p.index).join(", ")}`);
      throw new Error(`Could not find post for index ${c.post_index}`);
    }

    return {
      post_id: post.id, // Use Supabase UUID
      categories: c.categories,
      sentiment: c.sentiment,
      confidence: c.confidence,
      reasoning: c.reasoning,
    };
  });

  console.log(`✓ Successfully mapped ${classifications.length} classifications to Supabase IDs`);
  return classifications;
}

function calculateCost(inputTokens: number, outputTokens: number): string {
  // Claude 3.5 Haiku pricing:
  // Input: $0.80 per million tokens
  // Output: $4.00 per million tokens
  const inputCost = (inputTokens / 1_000_000) * 0.8;
  const outputCost = (outputTokens / 1_000_000) * 4.0;
  const totalCost = inputCost + outputCost;
  return `$${totalCost.toFixed(4)}`;
}

export async function POST(request: NextRequest) {
  console.log("=== CLASSIFY API CALLED ===");

  try {
    const body = await request.json();

    console.log("Received request body keys:", Object.keys(body));
    console.log("Number of posts received:", body.posts?.length || 0);
    console.log("Has API key:", !!body.anthropicApiKey);
    console.log("Has brand name:", !!body.brandName);

    if (!body.posts || !Array.isArray(body.posts) || body.posts.length === 0) {
      console.error("ERROR: No posts provided to classify!");
      return NextResponse.json(
        { success: false, error: "No posts provided", classifications: [], processed: 0 },
        { status: 400 }
      );
    }

    if (!body.anthropicApiKey) {
      console.error("ERROR: No Anthropic API key provided!");
      return NextResponse.json(
        { success: false, error: "Anthropic API key is required", classifications: [], processed: 0 },
        { status: 401 }
      );
    }

    console.log(`Processing ${body.posts.length} posts...`);
    console.log("First post sample:", {
      id: body.posts[0]?.id,
      text: body.posts[0]?.text?.substring(0, 100) + "...",
      hasText: !!body.posts[0]?.text
    });

    // Extract brand name from posts if available
    const brandName = body.brandName || "the brand";

    const allClassifications: PostClassification[] = [];
    const batches = Math.ceil(body.posts.length / BATCH_SIZE);
    let totalInputTokens = 0;
    let totalOutputTokens = 0;

    // Process in batches
    for (let i = 0; i < batches; i++) {
      const start = i * BATCH_SIZE;
      const end = Math.min(start + BATCH_SIZE, body.posts.length);
      const batch = body.posts.slice(start, end).map((post: PostToClassify, idx: number) => ({
        id: post.id, // Supabase UUID
        text: post.text,
        index: start + idx,
      }));

      console.log(`Processing batch ${i + 1}/${batches} (${batch.length} posts)`);
      console.log(`Batch post IDs: ${batch.map(p => p.id.substring(0, 8)).join(", ")}...`);

      try {
        const classifications = await classifyBatch(
          batch,
          brandName,
          body.anthropicApiKey
        );

        console.log(`Batch ${i + 1} classified successfully:`, classifications.length);
        console.log(`Sample classification:`, JSON.stringify(classifications[0], null, 2));

        allClassifications.push(...classifications);

        // Estimate token usage (rough estimate: ~4 chars per token)
        const batchText = batch.map((p) => p.text).join(" ");
        totalInputTokens += Math.ceil(batchText.length / 4) + 500; // +500 for prompt
        totalOutputTokens += classifications.length * 100; // ~100 tokens per classification

        // Rate limiting: wait 1 second between batches
        if (i < batches - 1) {
          console.log("Waiting 1 second before next batch...");
          await new Promise((resolve) => setTimeout(resolve, 1000));
        }
      } catch (error) {
        console.error(`Error processing batch ${i + 1}:`, error);
        // Continue with other batches instead of failing completely
        continue;
      }
    }

    const costEstimate = calculateCost(totalInputTokens, totalOutputTokens);

    console.log(`\n=== CLASSIFICATION COMPLETE ===`);
    console.log(`✓ Total classifications: ${allClassifications.length}`);
    console.log(`✓ Estimated cost: ${costEstimate}`);
    console.log(`✓ Total input tokens: ${totalInputTokens}`);
    console.log(`✓ Total output tokens: ${totalOutputTokens}`);
    console.log(`Classification post IDs:`, allClassifications.map(c => c.post_id.substring(0, 8)).join(", "));

    if (allClassifications.length > 0) {
      console.log("First classification sample:", JSON.stringify(allClassifications[0], null, 2));
    } else {
      console.error("WARNING: Returning 0 classifications!");
    }

    console.log("Returning response to client...");

    return NextResponse.json({
      success: true,
      classifications: allClassifications,
      processed: allClassifications.length,
      cost_estimate: costEstimate,
    });
  } catch (error) {
    console.error("=== CLASSIFICATION ERROR ===");
    console.error("Error classifying posts:", error);

    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Classification failed",
        classifications: [],
        processed: 0,
        cost_estimate: "$0.00",
      },
      { status: 500 }
    );
  }
}
