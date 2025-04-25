import os
import sys
from flask import Flask, jsonify, request, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from agent import scrape_jobs, match_profiles, get_paginated_matches
from supabase import create_client, Client
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure more visible logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Log to stdout for immediate visibility
        logging.FileHandler('app.log')      # Also log to file for persistence
    ]
)
logger = logging.getLogger(__name__)

# Print startup banner for visibility
print("\n" + "="*50)
print("STARTING GITHUB JOB MATCHER APPLICATION")
print("="*50 + "\n")

# Initialize Flask app
app = Flask(__name__)

# Initialize Supabase client
try:
    supabase_url = os.environ["SUPABASE_URL"]
    supabase_key = os.environ["SUPABASE_KEY"]
    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("✅ Supabase client initialized successfully")
except KeyError as e:
    logger.error(f"❌ Missing environment variable: {e}")
    print(f"ERROR: Missing environment variable: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"❌ Failed to initialize Supabase client: {e}")
    print(f"ERROR: Failed to initialize Supabase client: {e}")
    sys.exit(1)

# Initialize scheduler
scheduler = BackgroundScheduler()

@app.route('/')
def index():
    logger.info("Serving index page")
    return render_template('index.html')

@app.route('/scrape_jobs', methods=['GET'])
def scrape_jobs_route():
    """Endpoint to trigger job scraping"""
    try:
        print("🔍 Starting job scraping process...")
        logger.info("Starting job scraping...")
        jobs = scrape_jobs()              # scrape_jobs() returns a list
        count = len(jobs)
        logger.info(f"Job scraping completed. Scraped {count} jobs.")
        print(f"✅ Job scraping completed successfully. Found {count} jobs.")
        return jsonify({
            "success": True,
            "scraped": count,
            "jobs":    jobs
        })
    except Exception as e:
        error_msg = f"Error during job scraping: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return jsonify({"success": False, "error": error_msg}), 500

@app.route('/match_profiles', methods=['POST'])
def match_profiles_route():
    """Endpoint to trigger profile matching with pagination"""
    try:
        page     = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        if request.args.get('run', 'false').lower() == 'true':
            print("🔄 Starting profile matching process...")
            logger.info("Starting profile matching...")
            matches = match_profiles()
            match_count = len(matches) if isinstance(matches, list) else 0
            logger.info(f"Profile matching completed. Created {match_count} matches.")
            print(f"✅ Profile matching completed. Created {match_count} matches.")

        result = get_paginated_matches(page, per_page)
        return jsonify({
            "success": True,
            **result
        })
    except Exception as e:
        error_msg = f"Error during profile matching: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return jsonify({"success": False, "error": error_msg}), 500

@app.route('/profiles', methods=['GET'])
def get_profiles():
    """Endpoint to get all profiles"""
    try:
        print("📊 Fetching profiles...")
        resp = supabase.table("profiles").select("*").execute()
        profile_count = len(resp.data)
        print(f"✅ Successfully fetched {profile_count} profiles")
        return jsonify({"success": True, "profiles": resp.data, "count": profile_count})
    except Exception as e:
        error_msg = f"Error fetching profiles: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return jsonify({"success": False, "error": error_msg}), 500

@app.route('/jobs', methods=['GET'])
def get_jobs():
    """Endpoint to get all jobs"""
    try:
        print("📊 Fetching jobs...")
        resp = supabase.table("jobs").select("*").execute()
        job_count = len(resp.data)
        print(f"✅ Successfully fetched {job_count} jobs")
        return jsonify({"success": True, "jobs": resp.data, "count": job_count})
    except Exception as e:
        error_msg = f"Error fetching jobs: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return jsonify({"success": False, "error": error_msg}), 500

def scheduled_job_scrape():
    """Background job: daily scrape at midnight UTC."""
    with app.app_context():
        try:
            print("⏰ Running scheduled job scraping...")
            logger.info("Running scheduled job scraping...")
            jobs = scrape_jobs()
            job_count = len(jobs) if isinstance(jobs, list) else 0
            logger.info(f"Scheduled job scraping completed. Found {job_count} jobs.")
            print(f"✅ Scheduled job scraping completed. Found {job_count} jobs.")
        except Exception as e:
            error_msg = f"Error during scheduled job scraping: {str(e)}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")

# Schedule daily scrape at 00:00 UTC
scheduler.add_job(
    scheduled_job_scrape,
    trigger=CronTrigger(hour=0, minute=0),
    id='daily_job_scrape',
    replace_existing=True
)

# Add routes for checking application status
@app.route('/status', methods=['GET'])
def get_status():
    """Endpoint to check application status"""
    try:
        return jsonify({
            "success": True,
            "status": "running",
            "scheduler_running": scheduler.running,
            "scheduler_jobs": [
                {"id": job.id, "next_run_time": str(job.next_run_time)}
                for job in scheduler.get_jobs()
            ]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Start scheduler exactly once per process
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")
        print("⏰ Background job scheduler started successfully")

    # Print routes for visibility
    print("\n📋 Available API Routes:")
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            print(f"   • {rule.methods} {rule.rule} → {rule.endpoint}")
    print("\n")

    # Disable the reloader to avoid double scheduler starts
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Flask application on http://0.0.0.0:{port}")
    
    app.run(
        debug=True,
        use_reloader=False,
        host='0.0.0.0',
        port=port
    )
