"use client"

import { useState, useRef } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Upload, FileText, X, CheckCircle } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { uploadResume } from "@/lib/api"

export function ResumeUpload() {
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isUploaded, setIsUploaded] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()

  const handleFileSelect = (selectedFile: File) => {
    if (selectedFile.type !== "application/pdf") {
      toast({
        title: "Invalid file type",
        description: "Please upload a PDF file.",
        variant: "destructive",
      })
      return
    }

    if (selectedFile.size > 5 * 1024 * 1024) {
      // 5MB limit
      toast({
        title: "File too large",
        description: "Please upload a file smaller than 5MB.",
        variant: "destructive",
      })
      return
    }

    setFile(selectedFile)
    setIsUploaded(false)
  }

  const handleUpload = async () => {
    if (!file) return

    setIsUploading(true)

    try {
      const result = await uploadResume(file)

      setIsUploaded(true)
      toast({
        title: "Resume uploaded successfully!",
        description: "Your resume has been processed for personalized questions.",
      })
    } catch (error) {
      console.error("Upload error:", error)
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "Please try again later.",
        variant: "destructive",
      })
    } finally {
      setIsUploading(false)
    }
  }

  const removeFile = () => {
    setFile(null)
    setIsUploaded(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  return (
    <div className="space-y-4">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
        className="hidden"
      />

      {!file ? (
        <motion.div
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="border-2 border-dashed border-border rounded-lg p-8 text-center cursor-pointer hover:border-primary/50 transition-colors duration-200"
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-sm text-muted-foreground mb-2">Click to upload your resume</p>
          <p className="text-xs text-muted-foreground">PDF files only, max 5MB</p>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="border border-border rounded-lg p-4"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="h-8 w-8 text-primary" />
              <div>
                <p className="text-sm font-medium text-foreground">{file.name}</p>
                <p className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {isUploaded && <CheckCircle className="h-5 w-5 text-green-500" />}
              <Button variant="ghost" size="sm" onClick={removeFile} className="h-8 w-8 p-0">
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {!isUploaded && (
            <div className="mt-4">
              <Button onClick={handleUpload} disabled={isUploading} className="w-full">
                {isUploading ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
                    className="h-4 w-4 border-2 border-current border-t-transparent rounded-full mr-2"
                  />
                ) : null}
                {isUploading ? "Uploading..." : "Upload Resume"}
              </Button>
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}
