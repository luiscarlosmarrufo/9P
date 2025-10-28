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
import { getSupabaseClientBrowser } from "@/lib/supabase";

export default function Home() {
  const router = useRouter();
  const [brandName, setBrandName] = useState("");
  const [timeRange, setTimeRange] = useState("7");
  const [isLoading, setIsLoading] = useState(false);

  const handleAnalyze = async () => {
    let analysisId: string | null = null;

    try {
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

      // Decode API keys from base64
      const decodedAnthropicKey = atob(anthropicKey);
      const decodedRedditClientId = atob(redditClientId);
      const decodedRedditClientSecret = atob(redditClientSecret);

      setIsLoading(true);
      toast.info("Starting analysis...");

      // Step 3: Calculate date range
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(endDate.getDate() - parseInt(timeRange));

      console.log("Starting analysis for:", brandName);
      console.log("Date range:", startDate.toISOString(), "to", endDate.toISOString());

      // Step 4: Create analysis record in Supabase FIRST
      const supabase = getSupabaseClientBrowser();

      toast("Creating analysis record...");
      const { data: analysis, error: analysisError } = await supabase
        .from("analyses")
        .insert({
          brand_name: brandName.trim(),
          date_range: `${timeRange}days`,
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
          status: "processing",
          total_posts: 0,
        })
        .select()
        .single();

      if (analysisError) {
        console.error("Failed to create analysis:", analysisError);
        toast.error(`Failed to create analysis: ${analysisError.message}`);
        return;
      }

      analysisId = analysis.id;
      console.log("Analysis created with ID:", analysisId);
      toast.success(`Analysis created! ID: ${analysisId}`);

      // Step 5: Fetch Reddit posts
      toast("Fetching Reddit posts...");
      const redditResponse = await fetch("/api/reddit/search", {
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

      const redditData = await redditResponse.json();

      if (!redditResponse.ok) {
        throw new Error(redditData.error || "Failed to fetch Reddit posts");
      }

      console.log("Reddit posts fetched:", redditData.total);

      if (redditData.total === 0) {
        toast.warning("No posts found for this brand in the selected time range");

        // Update analysis status to completed with 0 posts
        await supabase
          .from("analyses")
          .update({ status: "completed", total_posts: 0 })
          .eq("id", analysisId);

        setIsLoading(false);
        router.push(`/analysis/${analysisId}`);
        return;
      }

      toast.success(`Found ${redditData.total} posts`);

      // Step 6: Save posts to Supabase (use upsert to handle duplicates)
      toast("Saving posts to database...");
      const postsToInsert = redditData.posts.map((post: any) => ({
        source: post.source,
        post_id: post.id,
        text: post.text,
        author: post.author || "unknown",
        url: post.url,
        engagement: post.engagement || 0,
        timestamp: post.timestamp,
        subreddit: post.subreddit || null,
      }));

      // Use upsert to reuse existing posts
      const { data: savedPosts, error: postsError } = await supabase
        .from("posts")
        .upsert(postsToInsert, {
          onConflict: "post_id,source",
          ignoreDuplicates: false, // Update engagement/author if changed
        })
        .select();

      if (postsError) {
        console.error("Failed to save posts:", postsError);
        toast.error(`Failed to save posts: ${postsError.message}`);
        throw new Error(postsError.message);
      }

      console.log("Saved/updated posts:", savedPosts?.length);

      // Step 6b: Link posts to this analysis via junction table
      const analysisPostsToInsert = savedPosts!.map((post) => ({
        analysis_id: analysisId,
        post_id: post.id,
      }));

      const { error: junctionError } = await supabase
        .from("analysis_posts")
        .upsert(analysisPostsToInsert, {
          onConflict: "analysis_id,post_id",
          ignoreDuplicates: true,
        });

      if (junctionError) {
        console.error("Failed to link posts to analysis:", junctionError);
        toast.error(`Failed to link posts: ${junctionError.message}`);
        throw new Error(junctionError.message);
      }

      toast.success(`Saved/updated ${savedPosts?.length} posts to database`);

      // Step 7: Check which posts already have classifications
      console.log("=== CHECKING FOR EXISTING CLASSIFICATIONS ===");
      const postIds = savedPosts!.map((p) => p.id);

      const { data: existingClassifications, error: classCheckError } = await supabase
        .from("classifications")
        .select("post_id")
        .in("post_id", postIds);

      if (classCheckError) {
        console.error("Error checking classifications:", classCheckError);
      }

      const classifiedPostIds = new Set(existingClassifications?.map((c) => c.post_id) || []);
      const postsToClassify = savedPosts!.filter((p) => !classifiedPostIds.has(p.id));
      const alreadyClassified = savedPosts!.length - postsToClassify.length;

      console.log(`Posts already classified: ${alreadyClassified}`);
      console.log(`Posts needing classification: ${postsToClassify.length}`);

      if (alreadyClassified > 0) {
        toast.success(`♻️ Reusing ${alreadyClassified} existing classifications`);
      }

      // Step 8: Classify only new posts with Claude
      if (postsToClassify.length === 0) {
        console.log("✓ All posts already classified! Skipping Claude API call.");
        toast.success("All posts already classified - no API cost!");
      } else {
        console.log("=== CLASSIFICATION DEBUG ===");
        console.log("Posts to classify:", postsToClassify.map(p => ({
          id: p.id,
          text: p.text?.substring(0, 50)
        })));
        console.log("API key exists:", !!decodedAnthropicKey);
        console.log("API key length:", decodedAnthropicKey?.length);

        toast(`Classifying ${postsToClassify.length} new posts with AI... This may take 1-2 minutes`);

      try {
        const classifyResponse = await fetch("/api/classify", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            posts: postsToClassify, // Only send posts that need classification
            anthropicApiKey: decodedAnthropicKey,
            brandName: brandName.trim(),
          }),
        });

        console.log("Classify API response status:", classifyResponse.status);
        console.log("Classify API response ok:", classifyResponse.ok);

        if (!classifyResponse.ok) {
          const errorText = await classifyResponse.text();
          console.error("Classify API error response:", errorText);
          toast.error(`Classification failed: ${errorText}`);
          throw new Error(`Classification failed (${classifyResponse.status}): ${errorText}`);
        }

        const classifyData = await classifyResponse.json();
        console.log("Classify API response data:", classifyData);

        if (!classifyData.success) {
          console.error("Classification not successful:", classifyData);
          throw new Error("Classification failed: " + (classifyData.error || "Unknown error"));
        }

        const { classifications } = classifyData;
        console.log(`Got ${classifications?.length || 0} classifications`);

        if (classifications && classifications.length > 0) {
          console.log("First classification:", classifications[0]);
        } else {
          console.error("ERROR: No classifications returned!");
          toast.error("Classification returned 0 results");
          throw new Error("No classifications returned from API");
        }

        toast.success(`Classified ${classifyData.processed} posts`);
        toast.info(`Estimated cost: ${classifyData.cost_estimate}`);

        // Step 8: Save classifications to Supabase
        toast("Saving classifications to database...");

        // Classifications already have the correct Supabase UUIDs as post_id
        const classificationsToInsert = classifyData.classifications.map((c: any) => ({
          post_id: c.post_id, // Already a Supabase UUID from the API
          categories: c.categories,
          sentiment: c.sentiment,
          confidence: c.confidence,
          reasoning: c.reasoning,
        }));

        console.log(`Saving ${classificationsToInsert.length} classifications to database`);
        console.log("Sample classification to insert:", classificationsToInsert[0]);

        const { data: savedClassifications, error: classError } = await supabase
          .from("classifications")
          .upsert(classificationsToInsert, {
            onConflict: "post_id",
            ignoreDuplicates: false, // Update existing classifications
          })
          .select();

        if (classError) {
          console.error("Failed to save classifications:", classError);
          toast.error(`Failed to save classifications: ${classError.message}`);
          throw new Error(classError.message);
        }

        console.log(`Saved/updated ${savedClassifications?.length || 0} classifications`);
        toast.success(`Saved/updated ${savedClassifications?.length || 0} classifications`);
      } catch (classifyError) {
        console.error("Classification error:", classifyError);
        throw classifyError;
      }
    }

      // Step 9: Update analysis status to completed
      const { error: updateError } = await supabase
        .from("analyses")
        .update({
          status: "completed",
          total_posts: savedPosts?.length || 0,
          updated_at: new Date().toISOString(),
        })
        .eq("id", analysisId);

      if (updateError) {
        console.error("Failed to update analysis:", updateError);
      }

      // Step 10: Navigate to results dashboard
      toast.success("Analysis complete!");
      router.push(`/analysis/${analysisId}`);

    } catch (error) {
      console.error("Error analyzing brand:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to analyze brand";
      toast.error(errorMessage);

      // Update analysis status to failed if we have an ID
      if (analysisId) {
        try {
          const supabase = getSupabaseClientBrowser();
          await supabase
            .from("analyses")
            .update({ status: "failed" })
            .eq("id", analysisId);
        } catch (updateError) {
          console.error("Failed to update analysis status:", updateError);
        }
      }
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
