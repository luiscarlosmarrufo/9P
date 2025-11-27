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
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-900">
      <Navigation />
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-6xl mx-auto">
          {/* Hero Section */}
          <div className="text-center mb-16 mt-8">
            <div className="mb-6">
              <h1 className="text-8xl md:text-9xl font-black bg-gradient-to-r from-purple-400 via-fuchsia-400 to-purple-600 bg-clip-text text-transparent mb-4 tracking-tight">
                9P
              </h1>
              <p className="text-3xl md:text-4xl font-bold text-white mb-4">
                Social Analytics
              </p>
            </div>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
              Unlock deep insights into your brand&apos;s social media presence with AI-powered sentiment analysis
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            <Card className="bg-slate-900/50 border-purple-500/20 backdrop-blur">
              <CardHeader>
                <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center mb-3">
                  <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <CardTitle className="text-purple-100">9Ps Analysis</CardTitle>
                <CardDescription className="text-gray-400">
                  Classify posts across Product, Place, Price, Publicity, Post-consumption, Purpose, Partnerships, People, and Planet
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="bg-slate-900/50 border-purple-500/20 backdrop-blur">
              <CardHeader>
                <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center mb-3">
                  <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <CardTitle className="text-purple-100">Sentiment Tracking</CardTitle>
                <CardDescription className="text-gray-400">
                  Understand how people feel about your brand with AI-powered sentiment analysis (positive, neutral, negative)
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="bg-slate-900/50 border-purple-500/20 backdrop-blur">
              <CardHeader>
                <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center mb-3">
                  <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <CardTitle className="text-purple-100">Strategic Insights</CardTitle>
                <CardDescription className="text-gray-400">
                  Get actionable recommendations and identify opportunities to improve your brand strategy
                </CardDescription>
              </CardHeader>
            </Card>
          </div>

          {/* Main Input Card */}
          <Card className="max-w-2xl mx-auto bg-slate-900/80 border-purple-500/30 backdrop-blur shadow-2xl shadow-purple-500/10">
            <CardHeader className="space-y-1 pb-6">
              <CardTitle className="text-2xl font-bold text-center text-purple-100">
                Start Your Analysis
              </CardTitle>
              <CardDescription className="text-center text-gray-400 text-base">
                Enter a brand name and time range to analyze social media sentiment
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <Label htmlFor="brand-name" className="text-purple-100 text-base">Brand Name</Label>
                <Input
                  id="brand-name"
                  placeholder="e.g., Nike, Apple, Tesla, Starbucks..."
                  className="w-full h-12 bg-slate-800/50 border-purple-500/30 text-white placeholder:text-gray-500 focus:border-purple-500 focus:ring-purple-500/20"
                  value={brandName}
                  onChange={(e) => setBrandName(e.target.value)}
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-3">
                <Label htmlFor="time-range" className="text-purple-100 text-base">Time Range</Label>
                <Select value={timeRange} onValueChange={setTimeRange} disabled={isLoading}>
                  <SelectTrigger id="time-range" className="h-12 bg-slate-800/50 border-purple-500/30 text-white focus:border-purple-500 focus:ring-purple-500/20">
                    <SelectValue placeholder="Select time range" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-900 border-purple-500/30">
                    <SelectItem value="7">Last 7 days</SelectItem>
                    <SelectItem value="30">Last 30 days</SelectItem>
                    <SelectItem value="90">Last 90 days</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button
                className="w-full h-12 bg-gradient-to-r from-purple-600 to-fuchsia-600 hover:from-purple-700 hover:to-fuchsia-700 text-white font-semibold text-base shadow-lg shadow-purple-500/30"
                size="lg"
                onClick={handleAnalyze}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  "Analyze Brand"
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Info Section */}
          <div className="mt-16 text-center">
            <p className="text-gray-400 mb-4">Powered by Claude AI • Reddit API • Next.js</p>
            <div className="flex justify-center gap-4 text-sm text-gray-500">
              <span>✓ Real-time data</span>
              <span>✓ AI classification</span>
              <span>✓ Interactive dashboards</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
