"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Award, TrendingUp, Target, BookOpen, Home, Download, MessageCircle } from "lucide-react"
import { useSearchParams, useRouter } from "next/navigation"
import Link from "next/link"
import { apiCall } from "@/lib/api"

interface StagePerformance {
  score: number
  feedback: string
  strengths: string[]
  weaknesses: string[]
}

interface RecommendedActions {
  technical: string[]
  soft_skills: string[]
}

interface DetailedEvaluation {
  question_id: string
  question: string
  technical_score: number
  completeness_score: number
  communication_score: number
  depth_of_knowledge?: number
  problem_solving_score?: number
  verdict: string
  strengths: string[]
  weaknesses: string[]
  recommendations: string[]
  summary: string
}

interface FinalReport {
  technical_level: string
  key_strengths: string[]
  key_weaknesses: string[]
  recommended_actions: RecommendedActions
  stage_performance: {
    introduction_resume_stage?: StagePerformance
    technical_stage?: StagePerformance
    hr_stage?: StagePerformance
  }
  summary_text: string
}

interface Summary {
  evaluations?: DetailedEvaluation[]
  summary?: {
    technical_level: string
    key_strengths: string[]
    key_weaknesses: string[]
    recommended_actions: RecommendedActions
    stage_performance: {
      introduction_resume_stage?: StagePerformance
      technical_stage?: StagePerformance
      hr_stage?: StagePerformance
    }
    summary: string
  }
  error?: string
}

export default function SummaryPage() {
  const [summary, setSummary] = useState<Summary["summary"] | null>(null)
  const [evaluations, setEvaluations] = useState<DetailedEvaluation[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const searchParams = useSearchParams()
  const router = useRouter()
  const sessionId = searchParams.get("session")

  useEffect(() => {
    if (!sessionId) {
      setError("No session ID provided")
      router.push("/dashboard")
      return
    }

    fetchSummary()
  }, [sessionId, router])

  const fetchSummary = async () => {
    try {
      setError(null)
      console.log("Fetching summary for session:", sessionId)

      const response = await apiCall("/api/interview/summary", {
        method: "POST",
        body: { session_id: sessionId },
      })

      if (response.ok) {
        const data = await response.json()
        console.log("Summary data received:", data)

        setSummary(data.summary || null)
        setEvaluations(data.evaluations || [])
      } else {
        const errorText = await response.text()
        console.error("Backend error response:", errorText)
        throw new Error(`Server error (${response.status}): ${errorText}`)
      }
    } catch (error) {
      console.error("Error fetching summary:", error)
      if (error instanceof Error) {
        setError(error.message)
      } else {
        setError("Failed to fetch interview summary. Please try again.")
      }
    } finally {
      setIsLoading(false)
    }
  }

  const getScoreColor = (score: number | null | undefined) => {
    if (score === null || score === undefined) return "text-muted-foreground"
    if (score >= 8) return "text-green-500"
    if (score >= 6) return "text-yellow-500"
    return "text-red-500"
  }

  const getScoreLabel = (score: number | null | undefined) => {
    if (score === null || score === undefined) return "Not Provided"
    if (score >= 8) return "Excellent"
    if (score >= 6) return "Good"
    if (score >= 4) return "Fair"
    return "Needs Improvement"
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        ease: [0.25, 0.46, 0.45, 0.94],
      },
    },
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
          className="h-8 w-8 border-2 border-white border-t-transparent rounded-full"
        />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="max-w-md bg-card border-border">
          <CardContent className="p-8 text-center">
            <div className="text-red-400 mb-4">
              <svg className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Error Loading Summary</h3>
            <p className="text-gray-400 mb-4 text-sm">{error}</p>
            <div className="space-y-2">
              <Button onClick={fetchSummary} className="w-full bg-white text-black hover:bg-gray-100">
                Try Again
              </Button>
              <Link href="/dashboard">
                <Button
                  variant="outline"
                  className="w-full border-gray-600 text-white hover:bg-gray-800 bg-transparent"
                >
                  Return to Dashboard
                </Button>
              </Link>
            </div>
            {sessionId && <p className="text-xs text-gray-500 mt-4">Session ID: {sessionId}</p>}
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="max-w-md bg-card border-border">
          <CardContent className="p-8 text-center">
            <p className="text-gray-400">No summary data available.</p>
            <Link href="/dashboard">
              <Button className="mt-4 bg-white text-black hover:bg-gray-100">Return to Dashboard</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  const displayData = {
    technical_level: summary?.technical_level || "",
    key_strengths: summary?.key_strengths || [],
    key_weaknesses: summary?.key_weaknesses || [],
    recommended_actions: summary?.recommended_actions || { technical: [], soft_skills: [] },
    stage_performance: summary?.stage_performance || {},
    summary_text: summary?.summary || "",
  }

  const safeStagePerformance = displayData.stage_performance
  const safeKeyStrengths = displayData.key_strengths
  const safeKeyWeaknesses = displayData.key_weaknesses
  const safeRecommendedActions = displayData.recommended_actions

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6 }}
          className="max-w-4xl mx-auto"
        >
          <div className="text-center mb-8">
            <Award className="h-16 w-16 mx-auto text-white mb-4" />
            <h1 className="text-3xl font-bold text-white mb-2">Interview Complete!</h1>
            <p className="text-gray-400">Here's your comprehensive performance analysis</p>
          </div>

          {displayData.summary_text && typeof displayData.summary_text === "string" && (
            <div className="mb-8">
              <Card className="bg-card border-border">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-white">
                    <TrendingUp className="h-5 w-5" />
                    Performance Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-300 leading-relaxed">{String(displayData.summary_text)}</p>
                </CardContent>
              </Card>
            </div>
          )}

          {(safeKeyStrengths.length > 0 || safeKeyWeaknesses.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              {safeKeyStrengths.length > 0 && (
                <Card className="bg-card border-border">
                  <CardHeader>
                    <CardTitle className="text-green-400">Key Strengths</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {safeKeyStrengths.map((strength, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm text-gray-300">
                          <div className="w-2 h-2 bg-green-400 rounded-full mt-2 flex-shrink-0" />
                          {strength}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}

              {safeKeyWeaknesses.length > 0 && (
                <Card className="bg-card border-border">
                  <CardHeader>
                    <CardTitle className="text-yellow-400">Areas for Improvement</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {safeKeyWeaknesses.map((weakness, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm text-gray-300">
                          <div className="w-2 h-2 bg-yellow-400 rounded-full mt-2 flex-shrink-0" />
                          {weakness}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {(safeRecommendedActions.technical.length > 0 || safeRecommendedActions.soft_skills.length > 0) && (
            <div className="mb-8">
              <Card className="bg-card border-border">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-white">
                    <Target className="h-5 w-5" />
                    Recommended Actions
                  </CardTitle>
                  <p className="text-gray-400">Focus on these areas to improve your interview performance</p>
                </CardHeader>
                <CardContent className="space-y-6">
                  {safeRecommendedActions.technical.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-white mb-3">Technical Skills</h4>
                      <ul className="space-y-3">
                        {safeRecommendedActions.technical.map((action, index) => (
                          <li
                            key={index}
                            className="flex items-start gap-3 p-3 bg-gray-800/50 rounded-lg border border-gray-700"
                          >
                            <BookOpen className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-gray-300">{action}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {safeRecommendedActions.soft_skills.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-white mb-3">Soft Skills</h4>
                      <ul className="space-y-3">
                        {safeRecommendedActions.soft_skills.map((action, index) => (
                          <li
                            key={index}
                            className="flex items-start gap-3 p-3 bg-gray-800/50 rounded-lg border border-gray-700"
                          >
                            <MessageCircle className="h-5 w-5 text-green-400 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-gray-300">{action}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/dashboard">
              <Button size="lg" className="w-full sm:w-auto bg-white text-black hover:bg-gray-100">
                <Home className="h-4 w-4 mr-2" />
                Back to Dashboard
              </Button>
            </Link>

            <Button
              variant="outline"
              size="lg"
              className="w-full sm:w-auto border-gray-600 text-white hover:bg-gray-800 bg-transparent"
            >
              <Download className="h-4 w-4 mr-2" />
              Download Report
            </Button>

            <Button
              variant="outline"
              size="lg"
              className="w-full sm:w-auto border-gray-600 text-white hover:bg-gray-800 bg-transparent"
              onClick={() => router.push("/interview")}
            >
              Practice Again
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
