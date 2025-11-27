"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  PieChart, Pie, Cell, BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";
import { Download, ArrowLeft, ExternalLink, Loader2, Sparkles, AlertCircle, TrendingUp, Lightbulb, Filter, X } from "lucide-react";
import { getSupabaseClientBrowser } from "@/lib/supabase";
import { toast } from "sonner";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

interface PostWithClassification {
  id: string;
  text: string;
  author: string;
  subreddit: string | null;
  engagement: number;
  timestamp: string;
  url: string;
  source: string;
  classifications: {
    categories: string[];
    sentiment: "positive" | "neutral" | "negative";
    confidence: number;
    reasoning: string;
  } | null;
}

interface KeyFinding {
  title: string;
  severity: "critical" | "warning" | "opportunity";
  description: string;
  impact: string;
  evidence: string;
}

interface Recommendation {
  priority: "high" | "medium" | "low";
  category: string;
  action: string;
  rationale: string;
  expectedOutcome: string;
}

interface Opportunity {
  area: string;
  description: string;
  suggestion: string;
}

interface Insights {
  executiveSummary: string;
  keyFindings: KeyFinding[];
  recommendations: Recommendation[];
  opportunities: Opportunity[];
}

const SENTIMENT_COLORS = {
  positive: "#22c55e",
  neutral: "#94a3b8",
  negative: "#ef4444",
};

const CATEGORY_COLOR = "#3b82f6";

export default function AnalysisPage() {
  const params = useParams();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [posts, setPosts] = useState<PostWithClassification[]>([]);
  const [brandName, setBrandName] = useState("");
  const [dateRange, setDateRange] = useState("");
  const [analysisStatus, setAnalysisStatus] = useState("");
  const [insights, setInsights] = useState<Insights | null>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);

  // Filter states
  const [selectedSentiments, setSelectedSentiments] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [searchText, setSearchText] = useState("");

  useEffect(() => {
    loadAnalysisData();
  }, [params.id]);

  const loadAnalysisData = async () => {
    try {
      setLoading(true);
      const supabase = getSupabaseClientBrowser();
      const analysisId = params.id as string;

      console.log("Loading analysis:", analysisId);

      // Fetch analysis record
      const { data: analysis, error: analysisError } = await supabase
        .from("analyses")
        .select("*")
        .eq("id", analysisId)
        .single();

      if (analysisError) {
        console.error("Failed to load analysis:", analysisError);
        toast.error(`Failed to load analysis: ${analysisError.message}`);
        return;
      }

      console.log("=== FETCHING DATA FOR ANALYSIS ===");
      console.log("Analysis ID:", analysisId);
      console.log("Analysis:", analysis);
      setBrandName(analysis.brand_name);
      setDateRange(analysis.date_range);
      setAnalysisStatus(analysis.status);

      // Step 1: Get post IDs for this analysis via junction table
      const { data: analysisPostsData, error: junctionError } = await supabase
        .from("analysis_posts")
        .select("post_id")
        .eq("analysis_id", analysisId);

      if (junctionError) {
        console.error("Error fetching analysis posts:", junctionError);
        toast.error(`Failed to load analysis posts: ${junctionError.message}`);
        return;
      }

      if (!analysisPostsData || analysisPostsData.length === 0) {
        console.log("No posts found for this analysis");
        setPosts([]);
        toast.info("No posts found for this analysis");
        return;
      }

      const analysisPostIds = analysisPostsData.map((ap) => ap.post_id);
      console.log("Post IDs for this analysis:", analysisPostIds.slice(0, 3), "... (first 3)");

      // Step 2: Get ALL posts for these IDs
      const { data: postsData, error: postsError } = await supabase
        .from("posts")
        .select("*")
        .in("id", analysisPostIds)
        .order("engagement", { ascending: false });

      console.log("Posts fetched:", postsData?.length || 0);

      if (postsError) {
        console.error("Error fetching posts:", postsError);
        toast.error(`Failed to load posts: ${postsError.message}`);
        return;
      }

      // Step 3: Get ALL classifications for these posts
      const { data: classificationsData, error: classError } = await supabase
        .from("classifications")
        .select("*")
        .in("post_id", analysisPostIds);

      console.log("Classifications fetched:", classificationsData?.length || 0);
      console.log("Sample classification:", classificationsData?.[0]);

      if (classError) {
        console.error("Error fetching classifications:", classError);
      }

      // Step 4: Create a map for O(1) lookup
      const classificationMap = new Map();
      classificationsData?.forEach((c) => {
        classificationMap.set(c.post_id, c);
      });

      console.log("Classification map size:", classificationMap.size);

      // Step 5: Merge posts with their classifications
      const transformedPosts: PostWithClassification[] = postsData.map((post) => {
        const classification = classificationMap.get(post.id);

        return {
          id: post.id,
          text: post.text,
          author: post.author,
          subreddit: post.subreddit,
          engagement: post.engagement,
          timestamp: post.timestamp,
          url: post.url,
          source: post.source,
          classifications: classification
            ? {
                categories: classification.categories,
                sentiment: classification.sentiment,
                confidence: classification.confidence,
                reasoning: classification.reasoning,
              }
            : null,
        };
      });

      const classifiedCount = transformedPosts.filter((p) => p.classifications !== null).length;
      console.log(`✅ Successfully merged ${classifiedCount} of ${transformedPosts.length} posts with classifications`);

      // If no classifications found, log diagnostic info
      if (classifiedCount === 0 && postsData.length > 0) {
        console.error("❌ DIAGNOSTIC: No classifications matched!");
        console.error("First post ID:", postsData[0].id);
        console.error("First classification post_id:", classificationsData?.[0]?.post_id);
        console.error("Are they the same?", postsData[0].id === classificationsData?.[0]?.post_id);
        console.error("Post ID type:", typeof postsData[0].id);
        console.error("Classification post_id type:", typeof classificationsData?.[0]?.post_id);
      }

      setPosts(transformedPosts);
      toast.success(`Loaded ${transformedPosts.length} posts`);

      // Load insights if they exist
      await loadInsights();
    } catch (error) {
      console.error("Error loading analysis:", error);
      toast.error("Failed to load analysis data");
    } finally {
      setLoading(false);
    }
  };

  const loadInsights = async () => {
    try {
      const supabase = getSupabaseClientBrowser();
      const analysisId = params.id as string;

      const { data: insightsData, error } = await supabase
        .from("insights")
        .select("*")
        .eq("analysis_id", analysisId)
        .single();

      if (error) {
        if (error.code !== "PGRST116") {
          // PGRST116 = no rows returned, which is fine
          console.error("Error loading insights:", error);
        }
        return;
      }

      if (insightsData) {
        setInsights({
          executiveSummary: insightsData.executive_summary,
          keyFindings: insightsData.key_findings,
          recommendations: insightsData.recommendations,
          opportunities: insightsData.opportunities,
        });
        console.log("✓ Loaded existing insights");
      }
    } catch (error) {
      console.error("Error loading insights:", error);
    }
  };

  const generateInsights = async () => {
    try {
      setInsightsLoading(true);
      toast.info("Generating strategic insights... This may take 30-60 seconds");

      const anthropicKey = localStorage.getItem("anthropic_key");
      if (!anthropicKey) {
        toast.error("Please configure your API keys in Settings");
        router.push("/settings");
        return;
      }

      const decodedKey = atob(anthropicKey);

      // Calculate stats
      const postsWithClassifications = posts.filter((p) => p.classifications !== null);
      const sentimentBreakdown = postsWithClassifications.reduce(
        (acc, post) => {
          if (post.classifications) {
            acc[post.classifications.sentiment]++;
          }
          return acc;
        },
        { positive: 0, neutral: 0, negative: 0 }
      );

      const categoryBreakdown: Record<string, number> = postsWithClassifications.reduce(
        (acc, post) => {
          if (post.classifications?.categories) {
            post.classifications.categories.forEach((category) => {
              acc[category] = (acc[category] || 0) + 1;
            });
          }
          return acc;
        },
        {} as Record<string, number>
      );

      // Get top 10 posts by engagement
      const samplePosts = postsWithClassifications
        .sort((a, b) => b.engagement - a.engagement)
        .slice(0, 10)
        .map((post) => ({
          text: post.text,
          categories: post.classifications!.categories,
          sentiment: post.classifications!.sentiment,
          engagement: post.engagement,
        }));

      const response = await fetch("/api/insights", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          analysisId: params.id,
          brandName,
          stats: {
            totalPosts: posts.length,
            classified: postsWithClassifications.length,
            sentimentBreakdown,
            categoryBreakdown,
            timeRange: dateRange,
          },
          samplePosts,
          anthropicApiKey: decodedKey,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Failed to generate insights");
      }

      const data = await response.json();
      console.log("Insights generated:", data.insights);

      setInsights(data.insights);
      toast.success("Strategic insights generated!");
      toast.info(`Estimated cost: ${data.cost_estimate}`);

      // Save insights to Supabase
      const supabase = getSupabaseClientBrowser();
      console.log("Saving insights to Supabase for analysis:", params.id);

      const insightsToSave = {
        analysis_id: params.id,
        executive_summary: data.insights.executiveSummary,
        key_findings: data.insights.keyFindings,
        recommendations: data.insights.recommendations,
        opportunities: data.insights.opportunities,
      };

      console.log("Insights payload:", JSON.stringify(insightsToSave, null, 2));

      const { data: savedInsights, error: saveError } = await supabase
        .from("insights")
        .upsert(insightsToSave, {
          onConflict: "analysis_id",
        })
        .select()
        .single();

      if (saveError) {
        console.error("Error saving insights to Supabase:", saveError);
        console.error("Error details:", {
          message: saveError.message,
          details: saveError.details,
          hint: saveError.hint,
          code: saveError.code,
        });
        toast.error(`Insights generated but failed to save: ${saveError.message}`);
      } else {
        console.log("✓ Insights saved successfully to Supabase:", savedInsights);
        toast.success("Strategic insights saved to database!");
      }
    } catch (error) {
      console.error("Error generating insights:", error);
      toast.error(error instanceof Error ? error.message : "Failed to generate insights");
    } finally {
      setInsightsLoading(false);
    }
  };

  // Apply filters
  const filteredPosts = posts.filter((post) => {
    // Sentiment filter
    if (selectedSentiments.length > 0 && post.classifications) {
      if (!selectedSentiments.includes(post.classifications.sentiment)) {
        return false;
      }
    }

    // Category filter
    if (selectedCategories.length > 0 && post.classifications) {
      const hasSelectedCategory = post.classifications.categories.some((cat) =>
        selectedCategories.includes(cat)
      );
      if (!hasSelectedCategory) return false;
    }

    // Source filter
    if (selectedSources.length > 0) {
      if (!selectedSources.includes(post.source)) return false;
    }

    // Text search
    if (searchText.trim() !== "") {
      const searchLower = searchText.toLowerCase();
      const matchesText = post.text.toLowerCase().includes(searchLower);
      const matchesAuthor = post.author.toLowerCase().includes(searchLower);
      const matchesSubreddit = post.subreddit?.toLowerCase().includes(searchLower);
      if (!matchesText && !matchesAuthor && !matchesSubreddit) return false;
    }

    return true;
  });

  // Calculate metrics from filtered posts
  const totalPosts = posts.length;
  const filteredTotalPosts = filteredPosts.length;
  const postsWithClassifications = filteredPosts.filter((p) => p.classifications !== null);

  const sentimentBreakdown = postsWithClassifications.reduce(
    (acc, post) => {
      if (post.classifications) {
        acc[post.classifications.sentiment]++;
      }
      return acc;
    },
    { positive: 0, neutral: 0, negative: 0 }
  );

  const sentimentPercentages = {
    positive: totalPosts > 0 ? Math.round((sentimentBreakdown.positive / totalPosts) * 100) : 0,
    neutral: totalPosts > 0 ? Math.round((sentimentBreakdown.neutral / totalPosts) * 100) : 0,
    negative: totalPosts > 0 ? Math.round((sentimentBreakdown.negative / totalPosts) * 100) : 0,
  };

  const categoryBreakdown: Record<string, number> = postsWithClassifications.reduce(
    (acc, post) => {
      if (post.classifications?.categories) {
        post.classifications.categories.forEach((category) => {
          acc[category] = (acc[category] || 0) + 1;
        });
      }
      return acc;
    },
    {} as Record<string, number>
  );

  // Stacked bar chart data: sentiment breakdown per category
  const categorySentimentBreakdown: Record<string, { positive: number; neutral: number; negative: number }> = {};
  postsWithClassifications.forEach((post) => {
    if (post.classifications?.categories) {
      post.classifications.categories.forEach((category) => {
        if (!categorySentimentBreakdown[category]) {
          categorySentimentBreakdown[category] = { positive: 0, neutral: 0, negative: 0 };
        }
        categorySentimentBreakdown[category][post.classifications!.sentiment]++;
      });
    }
  });

  const stackedCategoryData = Object.entries(categorySentimentBreakdown)
    .map(([category, sentiments]) => ({
      category,
      positive: sentiments.positive,
      neutral: sentiments.neutral,
      negative: sentiments.negative,
      total: sentiments.positive + sentiments.neutral + sentiments.negative,
    }))
    .sort((a, b) => b.total - a.total);

  const categoryData = Object.entries(categoryBreakdown)
    .map(([category, count]) => ({ category, count }))
    .sort((a, b) => b.count - a.count);

  const mostMentionedCategory = categoryData[0]?.category || "N/A";

  // Radar chart data for 9Ps
  const radarData = Object.entries(categoryBreakdown).map(([category, count]) => ({
    category,
    value: count,
    fullMark: Math.max(...Object.values(categoryBreakdown)),
  }));

  const sentimentChartData = [
    { name: "Positive", value: sentimentBreakdown.positive, color: SENTIMENT_COLORS.positive },
    { name: "Neutral", value: sentimentBreakdown.neutral, color: SENTIMENT_COLORS.neutral },
    { name: "Negative", value: sentimentBreakdown.negative, color: SENTIMENT_COLORS.negative },
  ].filter((item) => item.value > 0);

  // Get unique values for filters
  const allSentiments = Array.from(new Set(posts.filter(p => p.classifications).map(p => p.classifications!.sentiment)));
  const allCategories = Array.from(new Set(posts.flatMap(p => p.classifications?.categories || [])));
  const allSources = Array.from(new Set(posts.map(p => p.source)));

  const getSentimentBadgeColor = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return "bg-green-900/50 text-green-300 border-green-500/50";
      case "negative":
        return "bg-red-900/50 text-red-300 border-red-500/50";
      default:
        return "bg-gray-800/50 text-gray-300 border-gray-500/50";
    }
  };

  const exportToCSV = () => {
    const headers = ["Text", "Author", "Source", "Categories", "Sentiment", "Confidence", "Engagement", "Date", "URL"];
    const rows = postsWithClassifications.map((post) => [
      post.text.replace(/,/g, ";"),
      post.author,
      post.source,
      post.classifications?.categories.join("; ") || "",
      post.classifications?.sentiment || "",
      post.classifications?.confidence || "",
      post.engagement,
      new Date(post.timestamp).toLocaleDateString(),
      post.url,
    ]);

    const csv = [headers, ...rows].map((row) => row.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${brandName}_analysis.csv`;
    link.click();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-purple-950 to-slate-900">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-purple-400" />
          <p className="text-xl text-gray-300">Loading analysis...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <Link href="/">
              <Button variant="outline" className="mb-4 border-purple-500/30 hover:bg-purple-500/10">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Home
              </Button>
            </Link>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-fuchsia-400 bg-clip-text text-transparent">
              {brandName} Analysis
            </h1>
            <p className="text-gray-400 mt-2">
              {dateRange} • Status: <span className="font-semibold text-purple-300">{analysisStatus}</span>
            </p>
          </div>
          <Button onClick={exportToCSV} disabled={totalPosts === 0} className="bg-purple-600 hover:bg-purple-700">
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
        </div>

        {totalPosts === 0 ? (
          <Card className="bg-slate-900/80 border-purple-500/30">
            <CardContent className="py-12 text-center">
              <p className="text-xl text-gray-300">No data found for this analysis</p>
              <p className="text-sm text-gray-400 mt-2">The analysis may still be processing or no posts were found.</p>
              <Button onClick={() => router.push("/")} className="mt-4 bg-purple-600 hover:bg-purple-700">
                Start New Analysis
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Strategic Insights Section */}
            <Card className="mb-8 border-2 border-purple-500/30 bg-gradient-to-br from-slate-900 to-purple-900/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-6 w-6 text-purple-400" />
                    <CardTitle className="text-2xl text-gray-100">Strategic Insights</CardTitle>
                  </div>
                  {insights ? (
                    <Button onClick={generateInsights} disabled={insightsLoading} variant="outline" className="border-purple-500/30 hover:bg-purple-500/10 text-gray-200">
                      {insightsLoading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Regenerating...
                        </>
                      ) : (
                        "Regenerate"
                      )}
                    </Button>
                  ) : (
                    <Button onClick={generateInsights} disabled={insightsLoading} className="bg-purple-600 hover:bg-purple-700">
                      {insightsLoading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <Sparkles className="mr-2 h-4 w-4" />
                          Generate AI Insights
                        </>
                      )}
                    </Button>
                  )}
                </div>
                <CardDescription className="text-gray-400">
                  AI-powered strategic recommendations based on your brand analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                {insights ? (
                  <div className="space-y-6">
                    {/* Executive Summary */}
                    <Alert className="bg-slate-800/50 border-purple-500/30">
                      <Lightbulb className="h-5 w-5 text-purple-400" />
                      <AlertTitle className="text-lg text-gray-100">Executive Summary</AlertTitle>
                      <AlertDescription className="text-base mt-2 text-gray-300">
                        {insights.executiveSummary}
                      </AlertDescription>
                    </Alert>

                    {/* Key Findings */}
                    <div>
                      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-100">
                        <AlertCircle className="h-5 w-5 text-purple-400" />
                        Key Findings
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {insights.keyFindings.map((finding, idx) => (
                          <Alert
                            key={idx}
                            className={
                              finding.severity === "critical"
                                ? "bg-red-900/30 border-red-500/50"
                                : finding.severity === "warning"
                                ? "bg-yellow-900/30 border-yellow-500/50"
                                : "bg-green-900/30 border-green-500/50"
                            }
                          >
                            <div className="space-y-2">
                              <div className="flex items-start justify-between">
                                <AlertTitle className="text-base font-semibold text-gray-100">
                                  {finding.title}
                                </AlertTitle>
                                <Badge
                                  variant="outline"
                                  className={
                                    finding.severity === "critical"
                                      ? "bg-red-900/50 text-red-300 border-red-500/50"
                                      : finding.severity === "warning"
                                      ? "bg-yellow-900/50 text-yellow-300 border-yellow-500/50"
                                      : "bg-green-900/50 text-green-300 border-green-500/50"
                                  }
                                >
                                  {finding.severity}
                                </Badge>
                              </div>
                              <p className="text-sm font-medium text-gray-300">{finding.description}</p>
                              <p className="text-sm text-gray-400">
                                <strong>Impact:</strong> {finding.impact}
                              </p>
                              <p className="text-xs text-gray-500">
                                <strong>Evidence:</strong> {finding.evidence}
                              </p>
                            </div>
                          </Alert>
                        ))}
                      </div>
                    </div>

                    {/* Recommendations */}
                    <div>
                      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-100">
                        <TrendingUp className="h-5 w-5 text-purple-400" />
                        Recommendations
                      </h3>
                      <div className="space-y-3">
                        {insights.recommendations.map((rec, idx) => (
                          <Card key={idx} className="bg-slate-800/50 border-purple-500/30">
                            <CardHeader className="pb-3">
                              <div className="flex items-start justify-between">
                                <div className="space-y-1">
                                  <div className="flex items-center gap-2">
                                    <Badge
                                      className={
                                        rec.priority === "high"
                                          ? "bg-red-600"
                                          : rec.priority === "medium"
                                          ? "bg-yellow-600"
                                          : "bg-blue-600"
                                      }
                                    >
                                      {rec.priority} priority
                                    </Badge>
                                    <Badge variant="outline" className="border-purple-500/30 text-gray-300">{rec.category}</Badge>
                                  </div>
                                  <CardTitle className="text-base text-gray-100">{rec.action}</CardTitle>
                                </div>
                              </div>
                            </CardHeader>
                            <CardContent className="space-y-2 text-sm">
                              <p className="text-gray-300">
                                <strong className="text-gray-200">Why:</strong> {rec.rationale}
                              </p>
                              <p className="text-gray-300">
                                <strong className="text-gray-200">Expected Outcome:</strong>{" "}
                                {rec.expectedOutcome}
                              </p>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>

                    {/* Opportunities */}
                    <div>
                      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-100">
                        <Lightbulb className="h-5 w-5 text-purple-400" />
                        Opportunities
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {insights.opportunities.map((opp, idx) => (
                          <Card key={idx} className="bg-slate-800/50 border-green-500/30">
                            <CardHeader className="pb-3">
                              <CardTitle className="text-base text-gray-100">{opp.area}</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2 text-sm">
                              <p className="text-gray-300">{opp.description}</p>
                              <p className="text-green-400 font-medium">
                                💡 {opp.suggestion}
                              </p>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="py-12 text-center">
                    <Sparkles className="h-12 w-12 mx-auto mb-4 text-purple-400" />
                    <p className="text-gray-300 mb-4">
                      Generate AI-powered strategic insights to get actionable recommendations for {brandName}
                    </p>
                    <p className="text-sm text-gray-400">
                      Claude will analyze your data and provide executive summary, key findings, recommendations, and opportunities
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Filters */}
            <Card className="mb-6 bg-slate-900/80 border-purple-500/30">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Filter className="h-5 w-5 text-purple-400" />
                    <CardTitle className="text-gray-100">Filters</CardTitle>
                  </div>
                  {(selectedSentiments.length > 0 || selectedCategories.length > 0 || selectedSources.length > 0 || searchText) && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-purple-500/30 hover:bg-purple-500/10 text-gray-200"
                      onClick={() => {
                        setSelectedSentiments([]);
                        setSelectedCategories([]);
                        setSelectedSources([]);
                        setSearchText("");
                      }}
                    >
                      <X className="mr-2 h-4 w-4" />
                      Clear All
                    </Button>
                  )}
                </div>
                <CardDescription className="text-gray-400">
                  Showing {filteredTotalPosts} of {totalPosts} posts
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {/* Search */}
                  <div>
                    <label className="text-sm font-medium mb-2 block text-gray-300">Search</label>
                    <input
                      type="text"
                      placeholder="Search text, author, subreddit..."
                      className="w-full px-3 py-2 border border-purple-500/30 rounded-md text-sm bg-slate-800 text-gray-200 placeholder-gray-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                      value={searchText}
                      onChange={(e) => setSearchText(e.target.value)}
                    />
                  </div>

                  {/* Sentiment Filter */}
                  <div>
                    <label className="text-sm font-medium mb-2 block text-gray-300">Sentiment</label>
                    <div className="flex flex-wrap gap-2">
                      {allSentiments.map((sentiment) => (
                        <Badge
                          key={sentiment}
                          variant={selectedSentiments.includes(sentiment) ? "default" : "outline"}
                          className={`cursor-pointer ${
                            selectedSentiments.includes(sentiment)
                              ? sentiment === "positive"
                                ? "bg-green-600 hover:bg-green-700"
                                : sentiment === "negative"
                                ? "bg-red-600 hover:bg-red-700"
                                : "bg-gray-600 hover:bg-gray-700"
                              : "border-purple-500/30 text-gray-300 hover:bg-purple-500/10"
                          }`}
                          onClick={() => {
                            setSelectedSentiments((prev) =>
                              prev.includes(sentiment)
                                ? prev.filter((s) => s !== sentiment)
                                : [...prev, sentiment]
                            );
                          }}
                        >
                          {sentiment}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Category Filter */}
                  <div>
                    <label className="text-sm font-medium mb-2 block text-gray-300">Categories</label>
                    <div className="flex flex-wrap gap-2 max-h-20 overflow-y-auto">
                      {allCategories.map((category) => (
                        <Badge
                          key={category}
                          variant={selectedCategories.includes(category) ? "default" : "outline"}
                          className={`cursor-pointer ${
                            selectedCategories.includes(category)
                              ? "bg-purple-600 hover:bg-purple-700"
                              : "border-purple-500/30 text-gray-300 hover:bg-purple-500/10"
                          }`}
                          onClick={() => {
                            setSelectedCategories((prev) =>
                              prev.includes(category)
                                ? prev.filter((c) => c !== category)
                                : [...prev, category]
                            );
                          }}
                        >
                          {category}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Source Filter */}
                  <div>
                    <label className="text-sm font-medium mb-2 block text-gray-300">Source</label>
                    <div className="flex flex-wrap gap-2">
                      {allSources.map((source) => (
                        <Badge
                          key={source}
                          variant={selectedSources.includes(source) ? "default" : "outline"}
                          className={`cursor-pointer ${
                            selectedSources.includes(source)
                              ? "bg-purple-600 hover:bg-purple-700"
                              : "border-purple-500/30 text-gray-300 hover:bg-purple-500/10"
                          }`}
                          onClick={() => {
                            setSelectedSources((prev) =>
                              prev.includes(source)
                                ? prev.filter((s) => s !== source)
                                : [...prev, source]
                            );
                          }}
                        >
                          {source}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <Card className="bg-slate-900/80 border-purple-500/30">
                <CardHeader className="pb-3">
                  <CardDescription className="text-gray-400">Total Posts</CardDescription>
                  <CardTitle className="text-3xl text-gray-100">{totalPosts}</CardTitle>
                </CardHeader>
              </Card>

              <Card className="bg-slate-900/80 border-purple-500/30">
                <CardHeader className="pb-3">
                  <CardDescription className="text-gray-400">Positive Sentiment</CardDescription>
                  <CardTitle className="text-3xl text-green-400">
                    {sentimentPercentages.positive}%
                  </CardTitle>
                </CardHeader>
              </Card>

              <Card className="bg-slate-900/80 border-purple-500/30">
                <CardHeader className="pb-3">
                  <CardDescription className="text-gray-400">Most Mentioned</CardDescription>
                  <CardTitle className="text-2xl text-gray-100">{mostMentionedCategory}</CardTitle>
                </CardHeader>
              </Card>

              <Card className="bg-slate-900/80 border-purple-500/30">
                <CardHeader className="pb-3">
                  <CardDescription className="text-gray-400">Time Period</CardDescription>
                  <CardTitle className="text-2xl text-gray-100">{dateRange}</CardTitle>
                </CardHeader>
              </Card>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Sentiment Distribution */}
              <Card className="bg-slate-900/80 border-purple-500/30">
                <CardHeader>
                  <CardTitle className="text-gray-100">Sentiment Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  {sentimentChartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={sentimentChartData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {sentimentChartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #a855f7', borderRadius: '0.5rem' }} />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[300px] flex items-center justify-center text-gray-400">
                      No sentiment data available
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Radar Chart - 9Ps Categories */}
              <Card className="bg-slate-900/80 border-purple-500/30">
                <CardHeader>
                  <CardTitle className="text-gray-100">9Ps Category Coverage</CardTitle>
                  <CardDescription className="text-gray-400">Visual representation of category distribution</CardDescription>
                </CardHeader>
                <CardContent>
                  {radarData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <RadarChart data={radarData}>
                        <PolarGrid stroke="#a855f7" opacity={0.3} />
                        <PolarAngleAxis dataKey="category" tick={{ fill: '#d1d5db' }} />
                        <PolarRadiusAxis angle={90} domain={[0, "dataMax"]} tick={{ fill: '#d1d5db' }} />
                        <Radar
                          name="Posts"
                          dataKey="value"
                          stroke="#a855f7"
                          fill="#a855f7"
                          fillOpacity={0.6}
                        />
                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #a855f7', borderRadius: '0.5rem' }} />
                      </RadarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[300px] flex items-center justify-center text-gray-400">
                      No category data available
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Stacked Bar Chart - Category Breakdown by Sentiment */}
            <Card className="mb-8 bg-slate-900/80 border-purple-500/30">
              <CardHeader>
                <CardTitle className="text-gray-100">9Ps Categories with Sentiment Breakdown</CardTitle>
                <CardDescription className="text-gray-400">See sentiment distribution within each category</CardDescription>
              </CardHeader>
              <CardContent>
                {stackedCategoryData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={stackedCategoryData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#a855f7" opacity={0.2} />
                      <XAxis type="number" tick={{ fill: '#d1d5db' }} />
                      <YAxis dataKey="category" type="category" width={120} tick={{ fill: '#d1d5db' }} />
                      <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #a855f7', borderRadius: '0.5rem' }} />
                      <Legend />
                      <Bar dataKey="positive" stackId="a" fill={SENTIMENT_COLORS.positive} name="Positive" />
                      <Bar dataKey="neutral" stackId="a" fill={SENTIMENT_COLORS.neutral} name="Neutral" />
                      <Bar dataKey="negative" stackId="a" fill={SENTIMENT_COLORS.negative} name="Negative" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[400px] flex items-center justify-center text-gray-400">
                    No category data available
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Posts Table */}
            <Card className="bg-slate-900/80 border-purple-500/30">
              <CardHeader>
                <CardTitle className="text-gray-100">Posts Analysis</CardTitle>
                <CardDescription className="text-gray-400">
                  {postsWithClassifications.length} of {totalPosts} posts classified
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-purple-500/30 hover:bg-purple-500/5">
                        <TableHead className="text-gray-300">Source</TableHead>
                        <TableHead className="text-gray-300">Text</TableHead>
                        <TableHead className="text-gray-300">Categories</TableHead>
                        <TableHead className="text-gray-300">Sentiment</TableHead>
                        <TableHead className="text-gray-300">Engagement</TableHead>
                        <TableHead className="text-gray-300">Date</TableHead>
                        <TableHead className="text-gray-300"></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredPosts.map((post) => (
                        <TableRow key={post.id} className="border-purple-500/30 hover:bg-purple-500/5">
                          <TableCell className="font-medium text-gray-200">{post.source}</TableCell>
                          <TableCell className="max-w-md text-gray-300">
                            <div className="line-clamp-2">{post.text}</div>
                          </TableCell>
                          <TableCell>
                            {post.classifications ? (
                              <div className="flex flex-wrap gap-1">
                                {post.classifications.categories.map((cat) => (
                                  <Badge key={cat} variant="outline" className="text-xs border-purple-500/30 text-gray-300">
                                    {cat}
                                  </Badge>
                                ))}
                              </div>
                            ) : (
                              <span className="text-gray-500 text-sm">Not classified</span>
                            )}
                          </TableCell>
                          <TableCell>
                            {post.classifications ? (
                              <Badge className={getSentimentBadgeColor(post.classifications.sentiment)}>
                                {post.classifications.sentiment}
                              </Badge>
                            ) : (
                              <span className="text-gray-500 text-sm">-</span>
                            )}
                          </TableCell>
                          <TableCell className="text-gray-300">{post.engagement}</TableCell>
                          <TableCell className="text-gray-300">
                            {new Date(post.timestamp).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <Link href={post.url} target="_blank">
                              <Button variant="ghost" size="sm" className="hover:bg-purple-500/10 text-gray-300">
                                <ExternalLink className="h-4 w-4" />
                              </Button>
                            </Link>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
