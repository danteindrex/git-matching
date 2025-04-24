import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { repoUrl, additionalInfo } = body

    // Call the Django backend
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/match/project-to-jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_url: repoUrl, additional_info: additionalInfo }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      return NextResponse.json(
        { error: errorData.error || "Failed to process repository" },
        { status: response.status },
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error: any) {
    console.error("Error in project-to-job matching:", error)
    return NextResponse.json(
      { error: error.message || "An error occurred while processing your request" },
      { status: 500 },
    )
  }
}
