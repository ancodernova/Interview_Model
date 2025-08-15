"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Upload, Play, FileText, Clock, Award, TrendingUp } from "lucide-react"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { ResumeUpload } from "@/components/resume-upload"
import { apiCall } from "@/lib/api"

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null)
  const [sessions, setSessions] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  const { toast } = useToast()

  useEffect(() => {
    const token = localStorage.getItem("token")
    if (!token) {
      router.push("/login")
      return
    }

    // TODO: Fetch user profile and sessions
    setUser({ name: "John Doe", email: "john@example.com" })
    setIsLoading(false)
  }, [router])

  const startInterview = async () => {
    try {
      const response = await apiCall("/api/interview/start", {
        method: "POST",
      })

      if (response.ok) {
        const data = await response.json()
        router.push(`/interview?session=${data.session_id}`)
      } else {
        throw new Error("Failed to start interview")
      }
    } catch (error) {
      toast({
        title: "Failed to start interview",
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

  if (isLoading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
          className="h-8 w-8 border-2 border-slate-300 border-t-slate-900 rounded-full"
        />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-4 py-8">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }}>
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-slate-900 mb-2">Welcome back, {user?.name}!</h1>
            <p className="text-slate-600">Ready to practice your interview skills?</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <Card className="bg-white border border-slate-200 hover:shadow-lg transition-all duration-300 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-slate-900">
                  <Play className="h-5 w-5" />
                  Start New Interview
                </CardTitle>
                <p className="text-slate-600">Begin a new AI-powered mock interview session</p>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={startInterview}
                  className="w-full bg-slate-900 text-white hover:bg-slate-800 py-3 font-medium shadow-md hover:shadow-lg transition-all duration-200"
                >
                  Start Interview
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-white border border-slate-200 hover:shadow-lg transition-all duration-300 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-slate-900">
                  <Upload className="h-5 w-5" />
                  Upload Resume
                </CardTitle>
                <p className="text-slate-600">Upload your resume for personalized questions</p>
              </CardHeader>
              <CardContent>
                <ResumeUpload />
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Card className="bg-white border border-slate-200 shadow-sm hover:shadow-md transition-all duration-200">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-600">Total Sessions</p>
                    <p className="text-2xl font-bold text-slate-900">12</p>
                  </div>
                  <Clock className="h-8 w-8 text-slate-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white border border-slate-200 shadow-sm hover:shadow-md transition-all duration-200">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-600">Average Score</p>
                    <p className="text-2xl font-bold text-slate-900">8.5/10</p>
                  </div>
                  <Award className="h-8 w-8 text-slate-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white border border-slate-200 shadow-sm hover:shadow-md transition-all duration-200">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-600">Improvement</p>
                    <p className="text-2xl font-bold text-slate-900">+15%</p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-slate-400" />
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="bg-white border border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-slate-900">
                <FileText className="h-5 w-5" />
                Recent Sessions
              </CardTitle>
              <p className="text-slate-600">Your latest interview practice sessions</p>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-slate-500">
                No sessions yet. Start your first interview to see your progress here!
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
