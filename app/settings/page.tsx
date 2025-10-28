"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface APIStatus {
  tested: boolean;
  valid: boolean;
  testing: boolean;
}

export default function SettingsPage() {
  const [anthropicKey, setAnthropicKey] = useState("");
  const [redditClientId, setRedditClientId] = useState("");
  const [redditClientSecret, setRedditClientSecret] = useState("");
  const [twitterToken, setTwitterToken] = useState("");

  const [anthropicStatus, setAnthropicStatus] = useState<APIStatus>({
    tested: false,
    valid: false,
    testing: false,
  });
  const [redditStatus, setRedditStatus] = useState<APIStatus>({
    tested: false,
    valid: false,
    testing: false,
  });

  const [saveMessage, setSaveMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  // Load saved keys on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedAnthropicKey = localStorage.getItem("anthropic_key");
      const savedRedditClientId = localStorage.getItem("reddit_client_id");
      const savedRedditClientSecret = localStorage.getItem("reddit_client_secret");
      const savedTwitterToken = localStorage.getItem("twitter_token");

      if (savedAnthropicKey) setAnthropicKey(atob(savedAnthropicKey));
      if (savedRedditClientId) setRedditClientId(atob(savedRedditClientId));
      if (savedRedditClientSecret) setRedditClientSecret(atob(savedRedditClientSecret));
      if (savedTwitterToken) setTwitterToken(atob(savedTwitterToken));
    }
  }, []);

  const testAnthropicConnection = async () => {
    setAnthropicStatus({ tested: false, valid: false, testing: true });
    setErrorMessage("");

    // Trim whitespace from API key
    const trimmedKey = anthropicKey.trim();

    console.log("Testing Anthropic API...");
    console.log("API Key length:", trimmedKey.length);
    console.log("API Key (first 10 chars):", trimmedKey.substring(0, 10) + "...");
    console.log("API Key (last 5 chars):", "..." + trimmedKey.substring(trimmedKey.length - 5));
    console.log("Expected length: ~108 characters");

    try {
      const response = await fetch("/api/test-anthropic", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ apiKey: trimmedKey }),
      });

      const data = await response.json();

      console.log("Response status:", response.status);
      console.log("Response data:", data);

      if (data.valid) {
        setAnthropicStatus({ tested: true, valid: true, testing: false });
        setErrorMessage("");
        console.log("✅ Anthropic API key is valid!");
      } else {
        setAnthropicStatus({ tested: true, valid: false, testing: false });
        const errorMsg = data.error || "API key validation failed";
        setErrorMessage(`Anthropic: ${errorMsg}`);
        console.error("❌ Anthropic API test failed:", errorMsg);
        console.error("Details:", data.details);
      }
    } catch (error) {
      console.error("Error testing Anthropic API:", error);

      let errorMsg = "Network error. Please check your connection.";
      if (error instanceof Error) {
        console.error("Error message:", error.message);
        console.error("Error stack:", error.stack);
        errorMsg = error.message;
      }

      setAnthropicStatus({ tested: true, valid: false, testing: false });
      setErrorMessage(`Anthropic: ${errorMsg}`);
    }
  };

  const testRedditConnection = async () => {
    setRedditStatus({ tested: false, valid: false, testing: true });
    setErrorMessage("");

    // Trim whitespace from credentials
    const trimmedClientId = redditClientId.trim();
    const trimmedClientSecret = redditClientSecret.trim();

    console.log("Testing Reddit API...");
    console.log("Client ID length:", trimmedClientId.length);
    console.log("Client ID (first 10 chars):", trimmedClientId.substring(0, 10) + "...");
    console.log("Client Secret length:", trimmedClientSecret.length);
    console.log("Client Secret (first 10 chars):", trimmedClientSecret.substring(0, 10) + "...");

    try {
      const response = await fetch("/api/test-reddit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          clientId: trimmedClientId,
          clientSecret: trimmedClientSecret,
        }),
      });

      const data = await response.json();

      console.log("Response status:", response.status);
      console.log("Response data:", data);

      if (data.valid) {
        setRedditStatus({ tested: true, valid: true, testing: false });
        setErrorMessage("");
        console.log("✅ Reddit credentials are valid!");
      } else {
        setRedditStatus({ tested: true, valid: false, testing: false });
        const errorMsg = data.error || "Credential validation failed";
        setErrorMessage(`Reddit: ${errorMsg}`);
        console.error("❌ Reddit API test failed:", errorMsg);
        console.error("Details:", data.details);
      }
    } catch (error) {
      console.error("Error testing Reddit API:", error);

      let errorMsg = "Network error. Please check your connection.";
      if (error instanceof Error) {
        console.error("Error message:", error.message);
        errorMsg = error.message;
      }

      setRedditStatus({ tested: true, valid: false, testing: false });
      setErrorMessage(`Reddit: ${errorMsg}`);
    }
  };

  const saveSettings = () => {
    if (typeof window !== "undefined") {
      // Trim all values before saving
      if (anthropicKey) {
        const trimmed = anthropicKey.trim();
        localStorage.setItem("anthropic_key", btoa(trimmed));
        console.log("Saved Anthropic key length:", trimmed.length);
      }
      if (redditClientId) {
        const trimmed = redditClientId.trim();
        localStorage.setItem("reddit_client_id", btoa(trimmed));
        console.log("Saved Reddit Client ID length:", trimmed.length);
      }
      if (redditClientSecret) {
        const trimmed = redditClientSecret.trim();
        localStorage.setItem("reddit_client_secret", btoa(trimmed));
        console.log("Saved Reddit Client Secret length:", trimmed.length);
      }
      if (twitterToken) {
        const trimmed = twitterToken.trim();
        localStorage.setItem("twitter_token", btoa(trimmed));
      }

      setSaveMessage("✅ Settings saved successfully!");
      setTimeout(() => setSaveMessage(""), 3000);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="mb-8">
          <Link href="/" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
            ← Back to Home
          </Link>
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            API Settings
          </h1>
          <p className="text-gray-600">
            Enter your API keys to enable data collection and analysis
          </p>
        </div>

        {/* Anthropic API Section */}
        <Card className="mb-6 shadow-lg">
          <CardHeader>
            <CardTitle>Anthropic API (Claude)</CardTitle>
            <CardDescription>
              Used for classifying posts and generating insights. Get your key at{" "}
              <a
                href="https://console.anthropic.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                console.anthropic.com
              </a>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="anthropic-key">API Key</Label>
              <Input
                id="anthropic-key"
                type="password"
                placeholder="sk-ant-..."
                value={anthropicKey}
                onChange={(e) => setAnthropicKey(e.target.value.trim())}
              />
            </div>
            <div className="flex items-center gap-3">
              <Button
                onClick={testAnthropicConnection}
                disabled={!anthropicKey || anthropicStatus.testing}
                variant="outline"
              >
                {anthropicStatus.testing ? "Testing..." : "Test Connection"}
              </Button>
              {anthropicStatus.tested && (
                <span className={anthropicStatus.valid ? "text-green-600" : "text-red-600"}>
                  {anthropicStatus.valid ? "✅ Valid" : "❌ Invalid"}
                </span>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Reddit API Section */}
        <Card className="mb-6 shadow-lg">
          <CardHeader>
            <CardTitle>Reddit API</CardTitle>
            <CardDescription>
              Used to fetch Reddit posts. Get credentials at{" "}
              <a
                href="https://www.reddit.com/prefs/apps"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                reddit.com/prefs/apps
              </a>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="reddit-client-id">Client ID</Label>
              <Input
                id="reddit-client-id"
                type="password"
                placeholder="Enter Reddit Client ID"
                value={redditClientId}
                onChange={(e) => setRedditClientId(e.target.value.trim())}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="reddit-client-secret">Client Secret</Label>
              <Input
                id="reddit-client-secret"
                type="password"
                placeholder="Enter Reddit Client Secret"
                value={redditClientSecret}
                onChange={(e) => setRedditClientSecret(e.target.value.trim())}
              />
            </div>
            <div className="flex items-center gap-3">
              <Button
                onClick={testRedditConnection}
                disabled={!redditClientId || !redditClientSecret || redditStatus.testing}
                variant="outline"
              >
                {redditStatus.testing ? "Testing..." : "Test Connection"}
              </Button>
              {redditStatus.tested && (
                <span className={redditStatus.valid ? "text-green-600" : "text-red-600"}>
                  {redditStatus.valid ? "✅ Valid" : "❌ Invalid"}
                </span>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Twitter API Section */}
        <Card className="mb-6 shadow-lg opacity-75">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Twitter API</CardTitle>
              <Badge variant="secondary">Coming Soon</Badge>
            </div>
            <CardDescription>Twitter integration coming soon</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="twitter-token">Bearer Token</Label>
              <Input
                id="twitter-token"
                type="password"
                placeholder="Twitter API key (coming soon)"
                value={twitterToken}
                onChange={(e) => setTwitterToken(e.target.value)}
                disabled
              />
            </div>
          </CardContent>
        </Card>

        {/* Error Message */}
        {errorMessage && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 font-medium">❌ {errorMessage}</p>
          </div>
        )}

        {/* Save Button */}
        <div className="flex items-center gap-4">
          <Button onClick={saveSettings} size="lg" className="px-8">
            Save Settings
          </Button>
          {saveMessage && <span className="text-green-600 font-medium">{saveMessage}</span>}
        </div>
      </div>
    </div>
  );
}
