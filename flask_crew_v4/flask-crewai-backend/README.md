# Job Matcher - Flask + CrewAI Backend

A Flask application that uses CrewAI with Gemini 2.0 Flash to scrape remote job listings and match them to GitHub profiles based on similarity scores.

## Features

- Daily scraping of 8 remote-only job sites
- GitHub profile repository analysis
- Matching jobs to profiles using Gemini 2.0 Flash AI
- Supabase database integration
- Simple web UI for testing

## Prerequisites

- Python 3.9+
- Supabase account
- Google Gemini API access
- GitHub API token

## Environment Variables

The application requires the following environment variables, which can be set in a `.env` file for local development:

\`\`\`
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=1
PORT=5000

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta

# GitHub API Configuration
GITHUB_TOKEN=your_github_personal_access_token
\`\`\`

## Installation

1. Clone the repository:
   \`\`\`
   git clone https://github.com/yourusername/job-matcher.git
   cd job-matcher
   \`\`\`

2. Install dependencies:
   \`\`\`
   pip install -r requirements.txt
   \`\`\`

3. Create a `.env` file with your environment variables (see above).

4. Initialize the Supabase schema:
   \`\`\`
   python supabase_setup.py
   \`\`\`

## Running the Application

Start the Flask server:
\`\`\`
python app.py
\`\`\`

The application will be available at http://localhost:5000

## Using the Test UI

1. Open your browser and navigate to http://localhost:5000
2. Use the tabs to navigate between Jobs, Profiles, and Matches
3. Click the "Scrape Jobs" button to start scraping remote job listings
4. Click the "Run Matching" button to match jobs to GitHub profiles
5. Use the pagination controls to browse through matches

## API Endpoints

- `GET /scrape_jobs`: Triggers job scraping
- `POST /match_profiles?page=1&per_page=10&run=true`: Triggers profile matching and returns paginated results
- `GET /profiles`: Returns all GitHub profiles
- `GET /jobs`: Returns all scraped jobs

## Scheduled Tasks

The application automatically scrapes jobs every day at midnight UTC using APScheduler.

## Adding GitHub Profiles

To add GitHub profiles for matching, insert them into the Supabase `profiles` table with the following structure:

\`\`\`sql
INSERT INTO profiles (github_username, repos) 
VALUES ('username', '{"repo1": {"readme": "content", "topics": ["topic1", "topic2"]}}');
\`\`\`

Alternatively, you can use the provided utility script:

\`\`\`
python add_profile.py <github_username>
\`\`\`

## License

MIT
