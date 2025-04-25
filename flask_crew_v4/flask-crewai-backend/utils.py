import os
import json
import requests
from bs4 import BeautifulSoup
from github import Github
from supabase import create_client, Client

# Initialize clients
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

github_token = os.environ.get("GITHUB_TOKEN")
github = Github(github_token)

def fetch_github_profile_data(username):
    """Fetch GitHub profile data including repos, READMEs, and topics"""
    try:
        # Get the user
        user = github.get_user(username)
        
        # Get repositories
        repos_data = {}
        for repo in user.get_repos():
            if not repo.fork and not repo.private:  # Only include non-fork, public repos
                try:
                    # Get README content if it exists
                    try:
                        readme_content = repo.get_readme().decoded_content.decode('utf-8')
                    except:
                        readme_content = ""
                    
                    # Get topics
                    topics = repo.get_topics()
                    
                    # Add to repos data
                    repos_data[repo.name] = {
                        "readme": readme_content,
                        "topics": topics,
                        "description": repo.description or "",
                        "language": repo.language or "",
                        "stars": repo.stargazers_count
                    }
                except Exception as e:
                    print(f"Error fetching data for repo {repo.name}: {str(e)}")
        
        return repos_data
    except Exception as e:
        print(f"Error fetching GitHub profile for {username}: {str(e)}")
        return {}

def add_github_profile(username):
    """Add a GitHub profile to the database"""
    try:
        # Fetch profile data
        repos_data = fetch_github_profile_data(username)
        
        if not repos_data:
            return {"success": False, "error": f"Could not fetch data for GitHub user {username}"}
        
        # Insert into database
        response = supabase.table("profiles").insert({
            "github_username": username,
            "repos": json.dumps(repos_data)
        }).execute()
        
        return {"success": True, "profile_id": response.data[0]["id"] if response.data else None}
    except Exception as e:
        return {"success": False, "error": str(e)}

def scrape_job_site(site_name, url, selectors):
    """Scrape a job site using the provided selectors"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        jobs = []
        job_elements = soup.select(selectors["job_element"])
        
        for job_element in job_elements:
            try:
                # Extract job details using selectors
                title_element = job_element.select_one(selectors["title"])
                title = title_element.text.strip() if title_element else "Unknown Title"
                
                description_element = job_element.select_one(selectors["description"])
                description = description_element.text.strip() if description_element else ""
                
                url_element = job_element.  if description_element else ""
                
                url_element = job_element.select_one(selectors["url"])
                job_url = url_element.get("href") if url_element else ""
                
                # Make sure URL is absolute
                if job_url and not job_url.startswith(("http://", "https://")):
                    if job_url.startswith("/"):
                        # Get base URL
                        base_url = "{0.scheme}://{0.netloc}".format(urllib.parse.urlparse(url))
                        job_url = base_url + job_url
                    else:
                        job_url = url + "/" + job_url
                
                # Check if job is remote
                is_remote = False
                if selectors.get("remote_indicator"):
                    remote_element = job_element.select_one(selectors["remote_indicator"])
                    is_remote = remote_element is not None and "remote" in remote_element.text.lower()
                else:
                    # If no specific remote indicator, check if "remote" is in the title or description
                    is_remote = "remote" in title.lower() or "remote" in description.lower()
                
                if is_remote:
                    jobs.append({
                        "title": title,
                        "description": description,
                        "url": job_url,
                        "source": site_name,
                        "location": "Remote"
                    })
            except Exception as e:
                print(f"Error extracting job from {site_name}: {str(e)}")
        
        return jobs
    except Exception as e:
        print(f"Error scraping {site_name}: {str(e)}")
        return []
