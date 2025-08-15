"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { MessageCircle } from "lucide-react"

interface Question {
  question_id: string
  question: string
  audio: string
  sample_answer: string
}

interface QuestionCardProps {
  question: Question
}

export function QuestionCard({ question }: QuestionCardProps) {
  const [showSample, setShowSample] = useState(false)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <Card className="border-slate-200 bg-white shadow-sm hover:shadow-md transition-all duration-300">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-black">
            <MessageCircle className="h-5 w-5 text-black" />
            Interview Question
          </CardTitle>
          <CardDescription className="text-slate-600">Listen carefully and prepare your answer</CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Question Text */}
          <div className="p-6 bg-slate-50 rounded-lg border border-slate-100">
            <p className="text-lg text-black leading-relaxed font-medium">{question.question}</p>
          </div>

          {/* Sample Answer Toggle */}
          <div className="border-t border-slate-200 pt-4">
            <Button
              onClick={() => setShowSample(!showSample)}
              variant="ghost"
              size="sm"
              className="text-black hover:text-black hover:bg-slate-100 font-medium"
            >
              {showSample ? "Hide" : "Show"} Sample Answer
            </Button>

            {showSample && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
                className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-100"
              >
                <p className="text-sm text-black mb-2 font-semibold">Sample Answer:</p>
                <p className="text-sm text-slate-700 leading-relaxed">{question.sample_answer}</p>
              </motion.div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
