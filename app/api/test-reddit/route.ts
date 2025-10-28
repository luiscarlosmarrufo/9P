import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const { clientId, clientSecret } = await request.json();

    if (!clientId || !clientSecret) {
      return NextResponse.json(
        { error: "Client ID and Client Secret are required" },
        { status: 400 }
      );
    }

    console.log("Testing Reddit API credentials...");

    // Get Reddit OAuth token
    const authString = Buffer.from(`${clientId}:${clientSecret}`).toString("base64");

    const response = await fetch("https://www.reddit.com/api/v1/access_token", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        Authorization: `Basic ${authString}`,
        "User-Agent": "9P Social Analytics/1.0",
      },
      body: "grant_type=client_credentials",
    });

    const data = await response.json();

    console.log("Reddit API response status:", response.status);
    console.log("Reddit API response:", data);

    if (!response.ok) {
      let errorMessage = "Unknown error";

      if (response.status === 401) {
        errorMessage = "Invalid credentials. Please check your Client ID and Secret.";
      } else if (response.status === 403) {
        errorMessage = "Access forbidden. Your credentials may not have the required permissions.";
      } else if (response.status === 429) {
        errorMessage = "Rate limit exceeded. Please try again later.";
      } else if (response.status >= 500) {
        errorMessage = "Reddit server error. Please try again later.";
      } else if (data.error) {
        errorMessage = data.error;
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

    // Check if we got an access token
    if (!data.access_token) {
      return NextResponse.json(
        {
          valid: false,
          error: "No access token received from Reddit",
          details: data,
        },
        { status: 400 }
      );
    }

    return NextResponse.json({
      valid: true,
      message: "Reddit credentials are valid!",
    });
  } catch (error) {
    console.error("Error testing Reddit API:", error);

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
