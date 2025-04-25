import os
from crewai import Agent, Task, Crew, tools, LLM
import json
from crewai_tools import ScrapeWebsiteTool,WebsiteSearchTool,SerplyJobSearchTool,ScrapflyScrapeWebsiteTool
from supabase import create_client, Client
from github import Github
from datetime import datetime
# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Initialize GitHub client
github_token = os.environ.get("GITHUB_TOKEN")
github = Github(github_token)

# Initialize tools
#web_tool = ScrapeWebsiteTool(apikey = os.environ.get("GEMINI_API_KEY"),)
gemini_tool = ScrapflyScrapeWebsiteTool(api_key="scp-live-2532d8e26fac44c499a14be19fdb4396")
#tool= SerplyJobSearchTool(apikey = os.environ.get("GEMINI_API_KEY"),)


# Configure LLM
llm = LLM(
    model="gemini/gemini-2.0-flash",
    api_key=os.environ.get("GEMINI_API_KEY"),
    
)

# Define the job scraper and matcher agent
job_matcher_agent = Agent(
    role="Job Matcher",
    goal="Daily scrape of 8 remote-only job sites and match to GitHub profiles by percentage similarity",
    backstory="An AI agent that scrapes remote job listings (title, description, URL, 'Remote' location) and matches them to developer GitHub profiles using Gemini similarity scores.",
    tools=[
        #web_tool, 
        gemini_tool],
    llm=llm,
    verbose=True
)

# Define the task for scraping jobs
scrape_jobs_task = Task(
    description="""
    1. Scrape the following job sites for Remote positions:
       - Indeed
       - LinkedIn
       - Monster
       - Glassdoor
       - ZipRecruiter
       - FlexJobs
       - AngelList
       - RemoteOK
    
    2. For each job, capture:
       - title
       - description
       - URL
       - source (which site it came from)
       - location (always "Remote")
    
    3. Insert each job into the Supabase 'jobs' table.
    
    4. Return a JSON array of all scraped jobs.
    """,
    expected_output="4. Return a JSON array of all scraped jobs.",
    agent=job_matcher_agent
)

# Define the task for matching jobs to profiles
match_profiles_task = Task(
    description="""
    1. Pull all jobs from the Supabase 'jobs' table.
    
    2. Pull all GitHub profiles from the Supabase 'profiles' table.
    
    3. For each job and profile combination:
       a. Extract the profile's repos data (README content and topics)
       b. Use Gemini to compute a percentage similarity score between the job description and the repo data
       c. Insert the match into the Supabase 'matches' table with:
          - job_id
          - profile_id
          - score_percent (a number between 0 and 100)
          - current timestamp
    
    4. Return a JSON array of all matches created.
    """,
    agent=job_matcher_agent,
    expected_output="Return a JSON array of all matches created."
)

# Create crews for different operations
scrape_crew = Crew(
    agents=[job_matcher_agent],
    tasks=[scrape_jobs_task],
    verbose=True
)

match_crew = Crew(
    agents=[job_matcher_agent],
    tasks=[match_profiles_task],
    verbose=True
)

# Helper functions for the Flask app
import json

def scrape_jobs():
    crew_output = scrape_crew.kickoff()
    return crew_output.json_dict or []

def match_profiles():
    crew_output = match_crew.kickoff()
    return crew_output.json_dict or []


def get_paginated_matches(page=1, per_page=10):
    """Get paginated matches from the database"""
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Query matches ordered by score_percent descending
    response = supabase.table("matches") \
        .select("*") \
        .order("score_percent", desc=True) \
        .range(offset, offset + per_page - 1) \
        .execute()
    
    # Get total count
    count_response = supabase.table("matches").select("*", count="exact").execute()
    total = count_response.count if hasattr(count_response, "count") else 0
    
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "matches": response.data
    }
