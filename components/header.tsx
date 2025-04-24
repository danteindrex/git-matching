"use client"

import { Button } from "@/components/ui/button"
import { MoonIcon, SunIcon, GithubIcon } from "lucide-react"
import { useTheme } from "next-themes"

export default function Header() {
  const { theme, setTheme } = useTheme()

  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GithubIcon className="h-6 w-6" />
          <span className="font-bold text-xl">GitHub-Job Matcher</span>
        </div>

        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Toggle theme"
        >
          {theme === "dark" ? <SunIcon className="h-5 w-5" /> : <MoonIcon className="h-5 w-5" />}
        </Button>
      </div>
    </header>
  )
}
