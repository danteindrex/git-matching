"use client"

import type React from "react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"

export default function JobForm() {
  const [jobTitle, setJobTitle] = useState("")
  const [jobDescription, setJobDescription] = useState("")
  const [jobUrl, setJobUrl] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!jobTitle || !jobDescription) {
      setError("Please fill in all required fields")
      return
    }

    setLoading(true)
    setError("")

    try {
      const response = await fetch("/api/match/job-to-project", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jobTitle, jobDescription, jobUrl }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || "Failed to process job posting")
      }

      const data = await response.json()

      // Refresh the results section
      router.refresh()

      // Scroll to results
      document.getElementById("results-section")?.scrollIntoView({ behavior: "smooth" })
    } catch (err: any) {
      setError(err.message || "An error occurred while processing your request")
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="job-title">Job Title</Label>
        <Input
          id="job-title"
          placeholder="e.g., Senior Frontend Developer"
          value={jobTitle}
          onChange={(e) => setJobTitle(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="job-url">Job Posting URL (Optional)</Label>
        <Input
          id="job-url"
          placeholder="e.g., https://company.com/careers/job-posting"
          value={jobUrl}
          onChange={(e) => setJobUrl(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="job-description">Job Description</Label>
        <Textarea
          id="job-description"
          placeholder="Paste the full job description here, including required skills and qualifications"
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          rows={8}
        />
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Analyzing Job Requirements...
          </>
        ) : (
          "Find Matching Projects"
        )}
      </Button>
    </form>
  )
}
