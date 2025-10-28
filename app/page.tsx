"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import Navigation from "@/app/components/Navigation";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const [brandName, setBrandName] = useState("");
  const [timeRange, setTimeRange] = useState("7");
  const [isLoading, setIsLoading] = useState(false);

  const handleAnalyze = async () => {
    // Step 1: Validate inputs
    if (!brandName.trim()) {
      toast.error("Please enter a brand name");
      return;
    }

    // Step 2: Check if API keys exist
    const anthropicKey = localStorage.getItem("anthropic_key");
    const redditClientId = localStorage.getItem("reddit_client_id");
    const redditClientSecret = localStorage.getItem("reddit_client_secret");

    if (!anthropicKey || !redditClientId || !redditClientSecret) {
      toast.error("Please configure your API keys in Settings");
      setTimeout(() => {
        router.push("/settings");
      }, 1500);
      return;
    }

    // Step 3: Show loading state
    setIsLoading(true);
    toast.info("Fetching Reddit posts...");

    try {
      // Step 4: Calculate date range
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(endDate.getDate() - parseInt(timeRange));

      // Decode API keys from base64
      const decodedAnthropicKey = atob(anthropicKey);
      const decodedRedditClientId = atob(redditClientId);
      const decodedRedditClientSecret = atob(redditClientSecret);

      console.log("Starting analysis for:", brandName);
      console.log("Date range:", startDate.toISOString(), "to", endDate.toISOString());

      // Step 5: Call Reddit API
      const response = await fetch("/api/reddit/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          brandName: brandName.trim(),
          startDate: startDate.toISOString(),
          endDate: endDate.toISOString(),
          clientId: decodedRedditClientId,
          clientSecret: decodedRedditClientSecret,
        }),
      });

      const data = await response.json();

      // Step 6: Handle response
      if (!response.ok) {
        throw new Error(data.error || "Failed to fetch Reddit posts");
      }

      console.log("Reddit posts fetched successfully:", data);
      console.log("Total posts:", data.total);
      console.log("Posts:", data.posts);

      toast.success(`Successfully fetched ${data.total} posts from Reddit!`);

      // TODO: Navigate to dashboard page (will build next)
      // router.push(`/dashboard?brand=${encodeURIComponent(brandName)}`);
    } catch (error) {
      console.error("Error analyzing brand:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to analyze brand";
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <Navigation />
      <div className="min-h-screen flex items-center justify-center pt-16">
      <Card className="w-full max-w-md mx-4 shadow-xl">
        <CardHeader className="space-y-1">
          <CardTitle className="text-3xl font-bold text-center bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            9P Social Analytics
          </CardTitle>
          <CardDescription className="text-center text-base">
            Analyze brand sentiment across social media
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="brand-name">Brand Name</Label>
            <Input
              id="brand-name"
              placeholder="e.g., Nike, Apple, Tesla"
              className="w-full"
              value={brandName}
              onChange={(e) => setBrandName(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="time-range">Time Range</Label>
            <Select value={timeRange} onValueChange={setTimeRange} disabled={isLoading}>
              <SelectTrigger id="time-range">
                <SelectValue placeholder="Select time range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7">7 days</SelectItem>
                <SelectItem value="30">30 days</SelectItem>
                <SelectItem value="90">90 days</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button
            className="w-full"
            size="lg"
            onClick={handleAnalyze}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              "Analyze Brand"
            )}
          </Button>
        </CardContent>
      </Card>
      </div>
    </div>
  );
}
