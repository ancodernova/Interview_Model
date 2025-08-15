"use client"

import { motion } from "framer-motion"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { AlertTriangle, CheckCircle, MessageSquare, TrendingUp, Target, Lightbulb, AlertCircle } from "lucide-react"

interface Evaluation {
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
  transcript?: string
  flagged_script?: boolean
}

interface EvaluationCardProps {
  evaluation: Evaluation
}

export function EvaluationCard({ evaluation }: EvaluationCardProps) {
  if (!evaluation) {
    return null
  }

  const getScoreColor = (score: number) => {
    if (score >= 8) return "text-green-500"
    if (score >= 6) return "text-yellow-500"
    return "text-red-500"
  }

  const getScoreLabel = (score: number) => {
    if (score >= 8) return "Excellent"
    if (score >= 6) return "Good"
    if (score >= 4) return "Fair"
    return "Needs Improvement"
  }

  const coreScores = [evaluation.technical_score, evaluation.completeness_score, evaluation.communication_score]
  const optionalScores = [evaluation.depth_of_knowledge, evaluation.problem_solving_score].filter(
    (score) => score !== undefined,
  ) as number[]

  const allScores = [...coreScores, ...optionalScores]
  const avgScore = Math.round(allScores.reduce((sum, score) => sum + score, 0) / allScores.length)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "backOut" }}
    >
      <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Answer Evaluation
              </CardTitle>
              <CardDescription>AI analysis of your interview response</CardDescription>
            </div>

            {evaluation.flagged_script && (
              <Badge variant="destructive" className="flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" />
                Script Detected
              </Badge>
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Transcript */}
          {evaluation.transcript && (
            <div>
              <h4 className="text-sm font-medium text-foreground mb-2 flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                Your Response
              </h4>
              <div className="p-4 bg-muted/30 rounded-lg border border-border/30">
                <p className="text-sm text-foreground leading-relaxed">{evaluation.transcript}</p>
              </div>
            </div>
          )}

          {/* Verdict */}
          <div>
            <h4 className="text-sm font-medium text-foreground mb-2">Overall Verdict</h4>
            <Badge variant="outline" className="text-sm px-3 py-1">
              {evaluation.verdict}
            </Badge>
          </div>

          <div>
            <h4 className="text-sm font-medium text-foreground mb-4">Performance Scores</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Core Scores */}
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 }}
                className="p-4 bg-muted/20 rounded-lg border border-border/20"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-foreground">Technical</span>
                  <span className={`text-sm font-bold ${getScoreColor(evaluation.technical_score)}`}>
                    {evaluation.technical_score}/10
                  </span>
                </div>
                <Progress value={evaluation.technical_score * 10} className="h-2 mb-2" />
                <span className={`text-xs ${getScoreColor(evaluation.technical_score)}`}>
                  {getScoreLabel(evaluation.technical_score)}
                </span>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2 }}
                className="p-4 bg-muted/20 rounded-lg border border-border/20"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-foreground">Completeness</span>
                  <span className={`text-sm font-bold ${getScoreColor(evaluation.completeness_score)}`}>
                    {evaluation.completeness_score}/10
                  </span>
                </div>
                <Progress value={evaluation.completeness_score * 10} className="h-2 mb-2" />
                <span className={`text-xs ${getScoreColor(evaluation.completeness_score)}`}>
                  {getScoreLabel(evaluation.completeness_score)}
                </span>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.3 }}
                className="p-4 bg-muted/20 rounded-lg border border-border/20"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-foreground">Communication</span>
                  <span className={`text-sm font-bold ${getScoreColor(evaluation.communication_score)}`}>
                    {evaluation.communication_score}/10
                  </span>
                </div>
                <Progress value={evaluation.communication_score * 10} className="h-2 mb-2" />
                <span className={`text-xs ${getScoreColor(evaluation.communication_score)}`}>
                  {getScoreLabel(evaluation.communication_score)}
                </span>
              </motion.div>

              {evaluation.depth_of_knowledge !== undefined && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.4 }}
                  className="p-4 bg-muted/20 rounded-lg border border-border/20"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-foreground">Depth of Knowledge</span>
                    <span className={`text-sm font-bold ${getScoreColor(evaluation.depth_of_knowledge)}`}>
                      {evaluation.depth_of_knowledge}/10
                    </span>
                  </div>
                  <Progress value={evaluation.depth_of_knowledge * 10} className="h-2 mb-2" />
                  <span className={`text-xs ${getScoreColor(evaluation.depth_of_knowledge)}`}>
                    {getScoreLabel(evaluation.depth_of_knowledge)}
                  </span>
                </motion.div>
              )}

              {evaluation.problem_solving_score !== undefined && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.5 }}
                  className="p-4 bg-muted/20 rounded-lg border border-border/20"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-foreground">Problem Solving</span>
                    <span className={`text-sm font-bold ${getScoreColor(evaluation.problem_solving_score)}`}>
                      {evaluation.problem_solving_score}/10
                    </span>
                  </div>
                  <Progress value={evaluation.problem_solving_score * 10} className="h-2 mb-2" />
                  <span className={`text-xs ${getScoreColor(evaluation.problem_solving_score)}`}>
                    {getScoreLabel(evaluation.problem_solving_score)}
                  </span>
                </motion.div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Strengths */}
            <div>
              <h4 className="text-sm font-medium text-foreground mb-3 flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                Strengths
              </h4>
              <div className="space-y-2">
                {evaluation.strengths.map((strength, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-start gap-2 text-sm text-foreground"
                  >
                    <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0" />
                    {strength}
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Weaknesses */}
            <div>
              <h4 className="text-sm font-medium text-foreground mb-3 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-yellow-500" />
                Areas for Improvement
              </h4>
              <div className="space-y-2">
                {evaluation.weaknesses.map((weakness, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-start gap-2 text-sm text-foreground"
                  >
                    <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2 flex-shrink-0" />
                    {weakness}
                  </motion.div>
                ))}
              </div>
            </div>
          </div>

          {/* Recommendations */}
          <div>
            <h4 className="text-sm font-medium text-foreground mb-3 flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-blue-500" />
              Recommendations
            </h4>
            <div className="space-y-2">
              {evaluation.recommendations.map((recommendation, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-start gap-3 p-3 bg-blue-50/50 dark:bg-blue-950/20 rounded-lg border border-blue-200/30 dark:border-blue-800/30"
                >
                  <Target className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-foreground">{recommendation}</span>
                </motion.div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-foreground mb-2 flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Detailed Analysis
            </h4>
            <div className="p-4 bg-accent/10 rounded-lg border border-accent/20">
              <p className="text-sm text-foreground leading-relaxed">{evaluation.summary}</p>
            </div>
          </div>

          {/* Overall Score */}
          <div className="pt-4 border-t border-border/30">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-foreground">Overall Score</span>
              <div className="flex items-center gap-2">
                <span className={`text-lg font-bold ${getScoreColor(avgScore)}`}>{avgScore}/10</span>
                <Badge variant={avgScore >= 8 ? "default" : avgScore >= 6 ? "secondary" : "destructive"}>
                  {getScoreLabel(avgScore)}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
