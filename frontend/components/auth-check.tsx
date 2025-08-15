"use client"

import type React from "react"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

interface AuthCheckProps {
  children: React.ReactNode
  redirectTo?: string
}

export function AuthCheck({ children, redirectTo = "/login" }: AuthCheckProps) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)
  const router = useRouter()

  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem("token")

      if (!token || token === "null" || token === "undefined") {
        setIsAuthenticated(false)
        router.push(redirectTo)
        return
      }

      // Basic JWT validation - check if it has the right structure
      try {
        const parts = token.split(".")
        if (parts.length !== 3) {
          throw new Error("Invalid token structure")
        }

        // Decode payload to check expiration
        const payload = JSON.parse(atob(parts[1]))
        const currentTime = Math.floor(Date.now() / 1000)

        if (payload.exp && payload.exp < currentTime) {
          throw new Error("Token expired")
        }

        setIsAuthenticated(true)
      } catch (error) {
        console.error("Token validation failed:", error)
        localStorage.removeItem("token")
        setIsAuthenticated(false)
        router.push(redirectTo)
      }
    }

    checkAuth()
  }, [router, redirectTo])

  if (isAuthenticated === null) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return <>{children}</>
}
