"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { GithubIcon, BriefcaseIcon, CheckCircle, XCircle, Loader2 } from "lucide-react"

type MatchResult = {
  id: number
  type: "job" | "project"
  title: string
  company?: string
  owner?: string
  matchScore: number
  keyMatches: string[]
  missingSkills: string[]
  description: string
  url: string
  explanation: string
}

export default function MatchResults() {
  const [results, setResults] = useState<MatchResult[]>([])
  const [activeTab, setActiveTab] = useState("all")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true)
        const response = await fetch("/api/matches")

        if (!response.ok) {
          throw new Error("Failed to fetch match results")
        }

        const data = await response.json()
        setResults(data.results || [])
      } catch (err: any) {
        setError(err.message || "An error occurred while fetching results")
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
  }, [])

  const filteredResults = activeTab === "all" ? results : results.filter((result) => result.type === activeTab)

  if (loading) {
    return (
      <div id="results-section" className="mt-12 flex justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading match results...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div id="results-section" className="mt-12">
        <Card className="border-red-200">
          <CardContent className="pt-6">
            <p className="text-red-500">{error}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div id="results-section" className="mt-12">
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-muted-foreground">
              No match results available yet. Submit a GitHub repository or job posting to get started.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div id="results-section" className="mt-12">
      <h2 className="text-2xl font-bold mb-6 text-center">Match Results</h2>

      <Tabs defaultValue="all" className="w-full max-w-4xl mx-auto" onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3 mb-8">
          <TabsTrigger value="all">All Results</TabsTrigger>
          <TabsTrigger value="job" className="flex items-center gap-2">
            <BriefcaseIcon className="h-4 w-4" />
            <span>Jobs</span>
          </TabsTrigger>
          <TabsTrigger value="project" className="flex items-center gap-2">
            <GithubIcon className="h-4 w-4" />
            <span>Projects</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-6">
          {filteredResults.map((result) => (
            <ResultCard key={result.id} result={result} />
          ))}
        </TabsContent>

        <TabsContent value="job" className="space-y-6">
          {filteredResults.map((result) => (
            <ResultCard key={result.id} result={result} />
          ))}
        </TabsContent>

        <TabsContent value="project" className="space-y-6">
          {filteredResults.map((result) => (
            <ResultCard key={result.id} result={result} />
          ))}
        </TabsContent>
      </Tabs>
    </div>
  )
}

function ResultCard({ result }: { result: MatchResult }) {
  const [expanded, setExpanded] = useState(false)

  const getScoreColor = (score: number) => {
    if (score >= 80) return "bg-green-500"
    if (score >= 60) return "bg-yellow-500"
    return "bg-red-500"
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-xl">{result.title}</CardTitle>
            <CardDescription>{result.type === "job" ? result.company : `GitHub: ${result.owner}`}</CardDescription>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{result.matchScore}%</div>
            <div className="text-xs text-muted-foreground">Match Score</div>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="mb-4">
          <Progress value={result.matchScore} className="h-2" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <h4 className="text-sm font-medium flex items-center gap-1 mb-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              Key Matches
            </h4>
            <div className="flex flex-wrap gap-2">
              {result.keyMatches.map((skill, index) => (
                <Badge key={index} variant="secondary">
                  {skill}
                </Badge>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium flex items-center gap-1 mb-2">
              <XCircle className="h-4 w-4 text-red-500" />
              Missing Skills
            </h4>
            <div className="flex flex-wrap gap-2">
              {result.missingSkills.map((skill, index) => (
                <Badge key={index} variant="outline">
                  {skill}
                </Badge>
              ))}
            </div>
          </div>
        </div>

        <div className="mb-4">
          <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
            {expanded
              ? result.description
              : `${result.description.substring(0, 150)}${result.description.length > 150 ? "..." : ""}`}
          </p>
          {result.description.length > 150 && (
            <Button variant="link" size="sm" className="p-0 h-auto" onClick={() => setExpanded(!expanded)}>
              {expanded ? "Show less" : "Show more"}
            </Button>
          )}
        </div>

        <div className="mb-4">
          <h4 className="text-sm font-medium mb-2">Match Explanation</h4>
          <p className="text-sm text-muted-foreground">{result.explanation}</p>
        </div>

        <Button asChild variant="outline" size="sm">
          <a href={result.url} target="_blank" rel="noopener noreferrer">
            {result.type === "job" ? "View Job Posting" : "View GitHub Repository"}
          </a>
        </Button>
      </CardContent>
    </Card>
  )
}
