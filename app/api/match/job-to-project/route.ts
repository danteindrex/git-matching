import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { jobTitle, jobDescription, jobUrl } = body

    // Call the Django backend
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/match/job-to-projects`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_title: jobTitle, job_description: jobDescription, job_url: jobUrl }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      return NextResponse.json(
        { error: errorData.error || "Failed to process job posting" },
        { status: response.status },
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error: any) {
    console.error("Error in job-to-project matching:", error)
    return NextResponse.json(
      { error: error.message || "An error occurred while processing your request" },
      { status: 500 },
    )
  }
}
