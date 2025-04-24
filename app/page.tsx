"use client"

import { useState } from "react"
import { ThemeProvider } from "@/components/theme-provider"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { GithubIcon, BriefcaseIcon } from "lucide-react"
import MatchResults from "@/components/match-results"
import JobForm from "@/components/job-form"
import ProjectForm from "@/components/project-form"
import Header from "@/components/header"

export default function Home() {
  const [activeTab, setActiveTab] = useState("project-to-job")

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <div className="min-h-screen bg-background">
        <Header />

        <main className="container mx-auto py-8 px-4">
          <Card className="w-full max-w-4xl mx-auto">
            <CardHeader>
              <CardTitle className="text-2xl font-bold text-center">AI-Powered GitHub Project & Job Matching</CardTitle>
              <CardDescription className="text-center">
                Match your GitHub projects with job opportunities or find candidates for your job postings
              </CardDescription>
            </CardHeader>

            <CardContent>
              <Tabs defaultValue="project-to-job" className="w-full" onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-2 mb-8">
                  <TabsTrigger value="project-to-job" className="flex items-center gap-2">
                    <GithubIcon className="h-4 w-4" />
                    <span>Find Jobs for Projects</span>
                  </TabsTrigger>
                  <TabsTrigger value="job-to-project" className="flex items-center gap-2">
                    <BriefcaseIcon className="h-4 w-4" />
                    <span>Find Projects for Jobs</span>
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="project-to-job">
                  <ProjectForm />
                </TabsContent>

                <TabsContent value="job-to-project">
                  <JobForm />
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          <MatchResults />
        </main>

        <footer className="py-6 border-t">
          <div className="container mx-auto px-4 text-center text-muted-foreground">
            <p>© 2024 GitHub-Job Matcher. Powered by CrewAI and Django.</p>
          </div>
        </footer>
      </div>
    </ThemeProvider>
  )
}
