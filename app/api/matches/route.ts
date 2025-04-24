import { NextResponse } from "next/server"

export async function GET() {
  try {
    // Call the Django backend
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/matches`, {
      headers: { "Content-Type": "application/json" },
    })

    if (!response.ok) {
      const errorData = await response.json()
      return NextResponse.json({ error: errorData.error || "Failed to fetch matches" }, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error: any) {
    console.error("Error fetching matches:", error)
    return NextResponse.json({ error: error.message || "An error occurred while fetching matches" }, { status: 500 })
  }
}
