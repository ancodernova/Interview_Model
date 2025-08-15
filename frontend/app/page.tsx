"use client"

import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Sparkles, ArrowRight, Users } from "lucide-react"
import Link from "next/link"
import { useEffect, useRef } from "react"

export default function LandingPage() {
  const heroRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const elements = document.querySelectorAll(".animate-on-load")
    elements.forEach((el, index) => {
      setTimeout(() => {
        el.classList.add("opacity-100", "translate-y-0")
      }, index * 200)
    })
  }, [])

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-6">
      <div className="max-w-4xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="mb-12"
        >
          <div className="relative inline-block">
            <Sparkles className="h-16 w-16 text-slate-800 mx-auto" />
          </div>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-5xl md:text-7xl font-bold text-slate-900 mb-8 leading-tight"
        >
          Elevate Your
          <br />
          Interview Experience
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="text-xl text-slate-600 mb-12 max-w-3xl mx-auto leading-relaxed"
        >
          Engage in dynamic interviews that empower you to shine. Get AI-powered insights, real-time feedback, and
          unlock your potential with our revolutionary platform.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link href="/register">
            <Button
              size="lg"
              className="bg-slate-900 text-white hover:bg-slate-800 px-8 py-3 text-lg font-medium rounded-lg transition-all duration-200 hover:scale-105 shadow-lg hover:shadow-xl"
            >
              Get Started
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>

          <Link href="/login">
            <Button
              variant="outline"
              size="lg"
              className="border-2 border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400 px-8 py-3 text-lg font-medium rounded-lg transition-all duration-200 hover:scale-105 bg-transparent"
            >
              Sign In
              <Users className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </motion.div>
      </div>
    </div>
  )
}
