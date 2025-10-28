import { NextRequest, NextResponse } from "next/server";
import { ANTHROPIC_MODEL, ANTHROPIC_API_VERSION } from "@/lib/constants";

export async function POST(request: NextRequest) {
  try {
    const { apiKey } = await request.json();

    if (!apiKey) {
      return NextResponse.json(
        { error: "API key is required" },
        { status: 400 }
      );
    }

    console.log("Testing Anthropic API key...");

    // Make request to Anthropic API
    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "x-api-key": apiKey,
        "anthropic-version": ANTHROPIC_API_VERSION,
        "content-type": "application/json",
      },
      body: JSON.stringify({
        model: ANTHROPIC_MODEL,
        max_tokens: 10,
        messages: [
          {
            role: "user",
            content: "Hi",
          },
        ],
      }),
    });

    const data = await response.json();

    console.log("Anthropic API response status:", response.status);
    console.log("Anthropic API response:", data);

    if (!response.ok) {
      // Handle different error types
      let errorMessage = "Unknown error";

      if (response.status === 401) {
        errorMessage = "Invalid API key. Please check your key and try again.";
      } else if (response.status === 403) {
        errorMessage = "Access forbidden. Your API key may not have the required permissions.";
      } else if (response.status === 429) {
        errorMessage = "Rate limit exceeded. Please try again later.";
      } else if (response.status >= 500) {
        errorMessage = "Anthropic server error. Please try again later.";
      } else if (data.error?.message) {
        errorMessage = data.error.message;
      }

      return NextResponse.json(
        {
          valid: false,
          error: errorMessage,
          details: data,
        },
        { status: response.status }
      );
    }

    return NextResponse.json({
      valid: true,
      message: "API key is valid!",
    });
  } catch (error) {
    console.error("Error testing Anthropic API:", error);

    let errorMessage = "Network error. Please check your connection.";

    if (error instanceof Error) {
      errorMessage = error.message;
    }

    return NextResponse.json(
      {
        valid: false,
        error: errorMessage,
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
