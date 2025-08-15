"use client"

import { useState, useEffect, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { SkipForward, MessageSquare, Loader2, Play, Mic } from "lucide-react"
import { useSearchParams, useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { QuestionCard } from "@/components/question-card"
import { AnswerRecorder } from "@/components/answer-recorder"
import { EvaluationCard } from "@/components/evaluation-card"
import { apiCall } from "@/lib/api"

interface Question {
  question_id: string
  question: string
  audio: string
  sample_answer: string
}

interface Evaluation {
  transcript: string
  scores: {
    technical: number
    communication: number
    confidence: number
  }
  feedback: string
  flagged_script: boolean
}

const TOTAL_QUESTIONS = 5

export default function InterviewPage() {
  const [sessionId, setSessionId] = useState<string>("")
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null)
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [questions, setQuestions] = useState<Question[]>([])
  const [answers, setAnswers] = useState<any[]>([])
  const [questionCount, setQuestionCount] = useState(0)

  const [isPlayingAudio, setIsPlayingAudio] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTimeLeft, setRecordingTimeLeft] = useState(120) // 2 minutes
  const [isProcessing, setIsProcessing] = useState(false)
  const [autoFlowActive, setAutoFlowActive] = useState(false)
  const [isTransitioning, setIsTransitioning] = useState(false)

  const audioRef = useRef<HTMLAudioElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null)
  const recordedChunksRef = useRef<Blob[]>([])

  const searchParams = useSearchParams()
  const router = useRouter()
  const { toast } = useToast()

  useEffect(() => {
    const session = searchParams.get("session")
    if (session) {
      setSessionId(session)
    } else {
      router.push("/dashboard")
    }
  }, [searchParams, router])

  useEffect(() => {
    if (isRecording && recordingTimeLeft > 0) {
      recordingTimerRef.current = setTimeout(() => {
        setRecordingTimeLeft((prev) => prev - 1)
      }, 1000)
    } else if (isRecording && recordingTimeLeft === 0) {
      stopRecordingAndSubmit()
    }

    return () => {
      if (recordingTimerRef.current) {
        clearTimeout(recordingTimerRef.current)
      }
    }
  }, [isRecording, recordingTimeLeft])

  const getStageFromQuestionCount = (count: number) => {
    if (count === 1) return "intro"
    if (count >= 2 && count <= 3) return "resume"
    if (count === 4) return "technical"
    if (count === 5) return "closing"
    return "general"
  }

  const askQuestion = async (topic = "general") => {
    if (!sessionId) return

    setIsLoading(true)
    setEvaluation(null)
    setAutoFlowActive(true)

    try {
      const currentStage = getStageFromQuestionCount(questionCount + 1)
      const response = await apiCall("/api/interview/ask", {
        method: "POST",
        body: { topic: currentStage, session_id: sessionId },
      })

      if (response.ok) {
        const data = await response.json()

        if (!data || data.interview_complete === true || !data.question) {
          await finishInterview()
          return
        }

        const question: Question = {
          question_id: data.question_id,
          question: data.question,
          audio: data.audio,
          sample_answer: data.sample_answer,
        }

        setCurrentQuestion(question)
        setQuestions((prev) => [...prev, question])
        setQuestionCount((prev) => prev + 1)

        setTimeout(() => {
          playQuestionAudio(question.audio)
        }, 500)
      } else {
        throw new Error("Failed to get question")
      }
    } catch (error) {
      toast({
        title: "Failed to get question",
        description: "Please try again later.",
        variant: "destructive",
      })
      setAutoFlowActive(false)
    } finally {
      setIsLoading(false)
    }
  }

  const playQuestionAudio = async (audioHex: string) => {
    try {
      setIsPlayingAudio(true)

      // Convert hex to audio blob
      const audioBytes = new Uint8Array(audioHex.match(/.{1,2}/g)!.map((byte) => Number.parseInt(byte, 16)))
      const audioBlob = new Blob([audioBytes], { type: "audio/wav" })
      const audioUrl = URL.createObjectURL(audioBlob)

      if (audioRef.current) {
        audioRef.current.src = audioUrl
        audioRef.current.onended = () => {
          setIsPlayingAudio(false)
          setTimeout(() => {
            startRecording()
          }, 1000)
        }
        await audioRef.current.play()
      }
    } catch (error) {
      console.error("Error playing audio:", error)
      setIsPlayingAudio(false)
      setTimeout(() => {
        startRecording()
      }, 1000)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      recordedChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTimeLeft(120) // Reset to 2 minutes

      toast({
        title: "Recording Started",
        description: "You have 2 minutes to answer the question.",
      })
    } catch (error) {
      console.error("Error starting recording:", error)
      toast({
        title: "Recording Error",
        description: "Could not access microphone.",
        variant: "destructive",
      })
    }
  }

  const stopRecordingAndSubmit = async () => {
    if (!mediaRecorderRef.current || !currentQuestion) return

    setIsRecording(false)
    setIsProcessing(true)

    mediaRecorderRef.current.stop()

    // Wait for the recording to be processed
    setTimeout(async () => {
      try {
        const audioBlob = new Blob(recordedChunksRef.current, { type: "audio/wav" })

        // Submit to backend
        const formData = new FormData()
        formData.append("audio", audioBlob, "answer.wav")
        formData.append("session_id", sessionId)
        formData.append("question_id", currentQuestion.question_id)

        const response = await apiCall("/api/interview/answer", {
          method: "POST",
          body: formData,
        })

        if (response.ok) {
          const answerData = await response.json()
          setAnswers((prev) => [...prev, answerData])

          toast({
            title: "Answer Submitted",
            description: "Moving to next question...",
          })

          setIsProcessing(false)
          setIsTransitioning(true)

          setTimeout(() => {
            setIsTransitioning(false)
            if (questionCount < TOTAL_QUESTIONS) {
              askQuestion()
            } else {
              finishInterview()
            }
          }, 2000)
        } else {
          throw new Error("Failed to submit answer")
        }
      } catch (error) {
        console.error("Error submitting answer:", error)
        toast({
          title: "Submission Error",
          description: "Failed to submit answer. Please try again.",
          variant: "destructive",
        })
        setAutoFlowActive(false)
      } finally {
        setIsProcessing(false)
        setIsTransitioning(false)
      }
    }, 1000)
  }

  const handleAnswerSubmitted = (answerData: any) => {
    setAnswers((prev) => [...prev, answerData])
    setEvaluation(null)
  }

  const finishInterview = async () => {
    if (!sessionId) return

    try {
      const response = await apiCall("/api/interview/summary", {
        method: "POST",
        body: { session_id: sessionId },
      })

      if (response.ok) {
        router.push(`/summary?session=${sessionId}`)
      } else {
        throw new Error("Failed to get summary")
      }
    } catch (error) {
      toast({
        title: "Failed to finish interview",
        description: "Please try again later.",
        variant: "destructive",
      })
    }
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

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  return (
    <div className="min-h-screen bg-white">
      <audio ref={audioRef} style={{ display: "none" }} />

      <AnimatePresence>
        {isTransitioning && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-white z-50 flex items-center justify-center"
          >
            <div className="text-center space-y-6">
              <div className="relative">
                <div className="h-20 w-20 mx-auto">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
                    className="h-20 w-20 border-4 border-slate-200 border-t-black rounded-full"
                  />
                </div>
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 1.5, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
                  className="absolute inset-0 h-20 w-20 mx-auto border-2 border-black/20 rounded-full"
                />
              </div>
              <div className="space-y-2">
                <motion.h2
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
                  className="text-2xl font-bold text-black"
                >
                  Preparing Next Question
                </motion.h2>
                <p className="text-slate-600">
                  Question {questionCount + 1} of {TOTAL_QUESTIONS}
                </p>
                <div className="flex items-center justify-center gap-1 mt-4">
                  {[0, 1, 2].map((i) => (
                    <motion.div
                      key={i}
                      animate={{ scale: [1, 1.5, 1], opacity: [0.3, 1, 0.3] }}
                      transition={{
                        duration: 1.5,
                        repeat: Number.POSITIVE_INFINITY,
                        delay: i * 0.2,
                        ease: "easeInOut",
                      }}
                      className="h-2 w-2 bg-black rounded-full"
                    />
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <motion.div initial="hidden" animate="visible" variants={containerVariants}>
          <motion.div variants={itemVariants} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h1 className="text-3xl font-bold text-black">Interview Session</h1>
                <p className="text-slate-600 mt-1">Session ID: {sessionId}</p>
                {questionCount > 0 && (
                  <p className="text-slate-600 mt-1">
                    Question {questionCount} of {TOTAL_QUESTIONS}
                  </p>
                )}
                {autoFlowActive && (
                  <div className="flex items-center gap-2 mt-2">
                    {isPlayingAudio && (
                      <div className="flex items-center gap-2 text-blue-600">
                        <Play className="h-4 w-4" />
                        <span className="text-sm font-medium">Playing question...</span>
                      </div>
                    )}
                    {isRecording && (
                      <div className="flex items-center gap-2 text-red-600">
                        <div className="recording-indicator">
                          <Mic className="h-4 w-4" />
                        </div>
                        <span className="text-sm font-medium">Recording: {formatTime(recordingTimeLeft)}</span>
                      </div>
                    )}
                    {isProcessing && (
                      <div className="flex items-center gap-2 text-green-600">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm font-medium">Processing answer...</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
              {questionCount > 0 && (
                <div className="w-full sm:w-64">
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-2 bg-blue-600 rounded-full transition-all duration-500 ease-out"
                      style={{ width: `${(questionCount / TOTAL_QUESTIONS) * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </motion.div>

          <motion.div variants={itemVariants}>
            {!currentQuestion ? (
              <Card className="bg-white border border-slate-200 shadow-sm hover:shadow-md transition-all duration-300">
                <CardHeader>
                  <CardTitle className="text-black text-center">
                    <MessageSquare className="h-16 w-16 mx-auto text-blue-600 mb-4" />
                    Ready to Start?
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-center space-y-4">
                  <p className="text-slate-600 font-medium">
                    Click the button below to start your 5-question interview
                  </p>
                  <p className="text-sm text-slate-500">
                    The interview will run automatically - questions will play and recording will start/stop
                    automatically
                  </p>
                  <Button
                    onClick={() => askQuestion()}
                    disabled={isLoading}
                    className="rounded-lg bg-black hover:bg-slate-800 text-white px-8 py-3 font-semibold transition-all duration-200 hover:scale-105"
                  >
                    {isLoading ? (
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
                        className="h-4 w-4 border-2 border-current border-t-transparent rounded-full mr-2"
                      />
                    ) : null}
                    {isLoading ? "Getting Question..." : "Start Automatic Interview"}
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <QuestionCard question={currentQuestion} />
            )}
          </motion.div>

          {autoFlowActive && currentQuestion && (
            <motion.div variants={itemVariants}>
              <Card className="bg-white border border-slate-200 shadow-sm">
                <CardContent className="p-6">
                  <div className="text-center space-y-4">
                    {isPlayingAudio && (
                      <div className="flex flex-col items-center gap-3">
                        <div className="h-16 w-16 rounded-full bg-blue-100 flex items-center justify-center">
                          <Play className="h-8 w-8 text-blue-600" />
                        </div>
                        <p className="text-black font-semibold text-lg">AI is asking the question...</p>
                        <p className="text-slate-600">Please listen carefully</p>
                      </div>
                    )}

                    {isRecording && (
                      <div className="flex flex-col items-center gap-3">
                        <div className="h-16 w-16 rounded-full bg-red-100 flex items-center justify-center">
                          <div className="recording-indicator">
                            <Mic className="h-8 w-8 text-red-600" />
                          </div>
                        </div>
                        <p className="text-black font-semibold text-lg">Recording your answer...</p>
                        <p className="text-slate-600">Time remaining: {formatTime(recordingTimeLeft)}</p>
                        <div className="w-full max-w-xs bg-slate-200 rounded-full h-3">
                          <div
                            className="bg-red-600 h-3 rounded-full transition-all duration-1000 ease-out"
                            style={{ width: `${((120 - recordingTimeLeft) / 120) * 100}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {isProcessing && (
                      <div className="flex flex-col items-center gap-3">
                        <div className="h-16 w-16 rounded-full bg-green-100 flex items-center justify-center">
                          <Loader2 className="h-8 w-8 text-green-600 animate-spin" />
                        </div>
                        <p className="text-black font-semibold text-lg">Processing your answer...</p>
                        <p className="text-slate-600">Analyzing your response</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {currentQuestion && (
            <motion.div variants={itemVariants}>
              <AnswerRecorder
                sessionId={sessionId}
                questionId={currentQuestion.question_id}
                sampleAnswer={currentQuestion.sample_answer}
                onAnswerSubmitted={handleAnswerSubmitted}
              />
            </motion.div>
          )}

          <AnimatePresence>
            {evaluation && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                variants={itemVariants}
              >
                <EvaluationCard evaluation={evaluation} />
              </motion.div>
            )}
          </AnimatePresence>

          {currentQuestion && !autoFlowActive && (
            <motion.div variants={itemVariants} className="flex flex-col items-center space-y-3">
              <div className="flex gap-4">
                {questionCount < TOTAL_QUESTIONS && (
                  <Button
                    onClick={() => askQuestion()}
                    disabled={isLoading}
                    className="rounded-lg bg-black hover:bg-slate-800 text-white px-6 font-semibold transition-all duration-200 hover:scale-105"
                  >
                    <SkipForward className="h-4 w-4 mr-2" />
                    Next Question
                  </Button>
                )}

                <Button
                  onClick={finishInterview}
                  className="rounded-lg bg-black hover:bg-slate-800 text-white px-6 font-semibold transition-all duration-200 hover:scale-105"
                >
                  Finish Interview
                </Button>
              </div>
              <div className="text-xs text-slate-500">Tip: Keep your answers clear and concise</div>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
