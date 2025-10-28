"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  PieChart, Pie, Cell, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts";
import { Download, ArrowLeft, ExternalLink, Loader2, Sparkles, AlertCircle, TrendingUp, Lightbulb } from "lucide-react";
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

  // Calculate metrics
  const totalPosts = posts.length;
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

  const categoryData = Object.entries(categoryBreakdown)
    .map(([category, count]) => ({ category, count }))
    .sort((a, b) => b.count - a.count);

  const mostMentionedCategory = categoryData[0]?.category || "N/A";

  const sentimentChartData = [
    { name: "Positive", value: sentimentBreakdown.positive, color: SENTIMENT_COLORS.positive },
    { name: "Neutral", value: sentimentBreakdown.neutral, color: SENTIMENT_COLORS.neutral },
    { name: "Negative", value: sentimentBreakdown.negative, color: SENTIMENT_COLORS.negative },
  ].filter((item) => item.value > 0);

  const getSentimentBadgeColor = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return "bg-green-100 text-green-800 border-green-200";
      case "negative":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-xl text-gray-700">Loading analysis...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <Link href="/">
              <Button variant="outline" className="mb-4">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Home
              </Button>
            </Link>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              {brandName} Analysis
            </h1>
            <p className="text-gray-600 mt-2">
              {dateRange} • Status: <span className="font-semibold">{analysisStatus}</span>
            </p>
          </div>
          <Button onClick={exportToCSV} disabled={totalPosts === 0}>
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
        </div>

        {totalPosts === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-xl text-gray-600">No data found for this analysis</p>
              <p className="text-sm text-gray-500 mt-2">The analysis may still be processing or no posts were found.</p>
              <Button onClick={() => router.push("/")} className="mt-4">
                Start New Analysis
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Strategic Insights Section */}
            <Card className="mb-8 border-2 border-purple-200 bg-gradient-to-br from-purple-50 to-blue-50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-6 w-6 text-purple-600" />
                    <CardTitle className="text-2xl">Strategic Insights</CardTitle>
                  </div>
                  {insights ? (
                    <Button onClick={generateInsights} disabled={insightsLoading} variant="outline">
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
                    <Button onClick={generateInsights} disabled={insightsLoading}>
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
                <CardDescription>
                  AI-powered strategic recommendations based on your brand analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                {insights ? (
                  <div className="space-y-6">
                    {/* Executive Summary */}
                    <Alert className="bg-white border-blue-200">
                      <Lightbulb className="h-5 w-5 text-blue-600" />
                      <AlertTitle className="text-lg">Executive Summary</AlertTitle>
                      <AlertDescription className="text-base mt-2">
                        {insights.executiveSummary}
                      </AlertDescription>
                    </Alert>

                    {/* Key Findings */}
                    <div>
                      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <AlertCircle className="h-5 w-5" />
                        Key Findings
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {insights.keyFindings.map((finding, idx) => (
                          <Alert
                            key={idx}
                            className={
                              finding.severity === "critical"
                                ? "bg-red-50 border-red-300"
                                : finding.severity === "warning"
                                ? "bg-yellow-50 border-yellow-300"
                                : "bg-green-50 border-green-300"
                            }
                          >
                            <div className="space-y-2">
                              <div className="flex items-start justify-between">
                                <AlertTitle className="text-base font-semibold">
                                  {finding.title}
                                </AlertTitle>
                                <Badge
                                  variant="outline"
                                  className={
                                    finding.severity === "critical"
                                      ? "bg-red-100 text-red-800 border-red-300"
                                      : finding.severity === "warning"
                                      ? "bg-yellow-100 text-yellow-800 border-yellow-300"
                                      : "bg-green-100 text-green-800 border-green-300"
                                  }
                                >
                                  {finding.severity}
                                </Badge>
                              </div>
                              <p className="text-sm font-medium">{finding.description}</p>
                              <p className="text-sm text-gray-600">
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
                      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <TrendingUp className="h-5 w-5" />
                        Recommendations
                      </h3>
                      <div className="space-y-3">
                        {insights.recommendations.map((rec, idx) => (
                          <Card key={idx} className="bg-white">
                            <CardHeader className="pb-3">
                              <div className="flex items-start justify-between">
                                <div className="space-y-1">
                                  <div className="flex items-center gap-2">
                                    <Badge
                                      className={
                                        rec.priority === "high"
                                          ? "bg-red-500"
                                          : rec.priority === "medium"
                                          ? "bg-yellow-500"
                                          : "bg-blue-500"
                                      }
                                    >
                                      {rec.priority} priority
                                    </Badge>
                                    <Badge variant="outline">{rec.category}</Badge>
                                  </div>
                                  <CardTitle className="text-base">{rec.action}</CardTitle>
                                </div>
                              </div>
                            </CardHeader>
                            <CardContent className="space-y-2 text-sm">
                              <p>
                                <strong className="text-gray-700">Why:</strong> {rec.rationale}
                              </p>
                              <p>
                                <strong className="text-gray-700">Expected Outcome:</strong>{" "}
                                {rec.expectedOutcome}
                              </p>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>

                    {/* Opportunities */}
                    <div>
                      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Lightbulb className="h-5 w-5" />
                        Opportunities
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {insights.opportunities.map((opp, idx) => (
                          <Card key={idx} className="bg-white border-green-200">
                            <CardHeader className="pb-3">
                              <CardTitle className="text-base">{opp.area}</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2 text-sm">
                              <p>{opp.description}</p>
                              <p className="text-green-700 font-medium">
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
                    <Sparkles className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                    <p className="text-gray-600 mb-4">
                      Generate AI-powered strategic insights to get actionable recommendations for {brandName}
                    </p>
                    <p className="text-sm text-gray-500">
                      Claude will analyze your data and provide executive summary, key findings, recommendations, and opportunities
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>Total Posts</CardDescription>
                  <CardTitle className="text-3xl">{totalPosts}</CardTitle>
                </CardHeader>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>Positive Sentiment</CardDescription>
                  <CardTitle className="text-3xl text-green-600">
                    {sentimentPercentages.positive}%
                  </CardTitle>
                </CardHeader>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>Most Mentioned</CardDescription>
                  <CardTitle className="text-2xl">{mostMentionedCategory}</CardTitle>
                </CardHeader>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>Time Period</CardDescription>
                  <CardTitle className="text-2xl">{dateRange}</CardTitle>
                </CardHeader>
              </Card>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Sentiment Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle>Sentiment Distribution</CardTitle>
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
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[300px] flex items-center justify-center text-gray-500">
                      No sentiment data available
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Category Breakdown */}
              <Card>
                <CardHeader>
                  <CardTitle>9Ps Category Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  {categoryData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={categoryData} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" />
                        <YAxis dataKey="category" type="category" width={120} />
                        <Tooltip />
                        <Bar dataKey="count" fill={CATEGORY_COLOR} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[300px] flex items-center justify-center text-gray-500">
                      No category data available
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Posts Table */}
            <Card>
              <CardHeader>
                <CardTitle>Posts Analysis</CardTitle>
                <CardDescription>
                  {postsWithClassifications.length} of {totalPosts} posts classified
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Source</TableHead>
                        <TableHead>Text</TableHead>
                        <TableHead>Categories</TableHead>
                        <TableHead>Sentiment</TableHead>
                        <TableHead>Engagement</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {posts.map((post) => (
                        <TableRow key={post.id}>
                          <TableCell className="font-medium">{post.source}</TableCell>
                          <TableCell className="max-w-md">
                            <div className="line-clamp-2">{post.text}</div>
                          </TableCell>
                          <TableCell>
                            {post.classifications ? (
                              <div className="flex flex-wrap gap-1">
                                {post.classifications.categories.map((cat) => (
                                  <Badge key={cat} variant="outline" className="text-xs">
                                    {cat}
                                  </Badge>
                                ))}
                              </div>
                            ) : (
                              <span className="text-gray-400 text-sm">Not classified</span>
                            )}
                          </TableCell>
                          <TableCell>
                            {post.classifications ? (
                              <Badge className={getSentimentBadgeColor(post.classifications.sentiment)}>
                                {post.classifications.sentiment}
                              </Badge>
                            ) : (
                              <span className="text-gray-400 text-sm">-</span>
                            )}
                          </TableCell>
                          <TableCell>{post.engagement}</TableCell>
                          <TableCell>
                            {new Date(post.timestamp).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <Link href={post.url} target="_blank">
                              <Button variant="ghost" size="sm">
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
