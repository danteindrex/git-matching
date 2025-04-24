"use client"

import type React from "react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"

export default function ProjectForm() {
  const [repoUrl, setRepoUrl] = useState("")
  const [additionalInfo, setAdditionalInfo] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!repoUrl) {
      setError("Please enter a GitHub repository URL")
      return
    }

    setLoading(true)
    setError("")

    try {
      const response = await fetch("/api/match/project-to-job", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repoUrl, additionalInfo }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || "Failed to process repository")
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
        <Label htmlFor="repo-url">GitHub Repository URL</Label>
        <Input
          id="repo-url"
          placeholder="https://github.com/username/repository"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="additional-info">Additional Information (Optional)</Label>
        <Textarea
          id="additional-info"
          placeholder="Add any additional skills, preferences, or information that might help with matching"
          value={additionalInfo}
          onChange={(e) => setAdditionalInfo(e.target.value)}
          rows={4}
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
            Analyzing Repository...
          </>
        ) : (
          "Find Matching Jobs"
        )}
      </Button>
    </form>
  )
}
