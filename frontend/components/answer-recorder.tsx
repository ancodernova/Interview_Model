"use client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Mic } from "lucide-react"

interface AnswerRecorderProps {
  sessionId: string
  questionId: string
  sampleAnswer: string
  onAnswerSubmitted: (evaluation: any) => void
}

export function AnswerRecorder({ sessionId, questionId, sampleAnswer, onAnswerSubmitted }: AnswerRecorderProps) {
  return (
    <Card className="border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-black">
          <Mic className="h-5 w-5 text-black" />
          Record Your Answer
        </CardTitle>
        <CardDescription className="text-slate-600">
          Recording will start automatically after the question is played
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Recording Tips */}
        <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
          <h4 className="text-sm font-semibold text-black mb-2">Recording Tips:</h4>
          <ul className="text-sm text-slate-600 space-y-1">
            <li>• The interview runs automatically - no manual controls needed</li>
            <li>• Speak clearly and at a normal pace</li>
            <li>• Find a quiet environment to minimize background noise</li>
            <li>• You have 2 minutes to answer each question</li>
            <li>• Recording will stop automatically and move to the next question</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  )
}
