import os
from supabase import create_client, Client

def setup_supabase_schema():
    """Set up the Supabase schema for the application"""
    # Get Supabase credentials from environment variables
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
    
    # Initialize Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Create jobs table
    jobs_query = """
    CREATE TABLE IF NOT EXISTS public.jobs (
      id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
      title        TEXT NOT NULL,
      description  TEXT NOT NULL,
      url          TEXT NOT NULL,
      source       TEXT NOT NULL,
      location     TEXT NOT NULL DEFAULT 'Remote',
      scraped_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Create profiles table
    profiles_query = """
    CREATE TABLE IF NOT EXISTS public.profiles (
      id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
      github_username TEXT UNIQUE NOT NULL,
      repos          JSONB NOT NULL,
      last_updated   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Create matches table
    matches_query = """
    CREATE TABLE IF NOT EXISTS public.matches (
      id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
      job_id        BIGINT REFERENCES public.jobs(id),
      profile_id    BIGINT REFERENCES public.profiles(id),
      score_percent REAL NOT NULL,
      matched_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Execute the queries
    try:
        # Using the REST API to execute SQL
        supabase.rpc('exec_sql', {'query': jobs_query}).execute()
        supabase.rpc('exec_sql', {'query': profiles_query}).execute()
        supabase.rpc('exec_sql', {'query': matches_query}).execute()
        
        print("Supabase schema created successfully!")
        return True
    except Exception as e:
        print(f"Error creating Supabase schema: {str(e)}")
        return False

if __name__ == "__main__":
    setup_supabase_schema()
