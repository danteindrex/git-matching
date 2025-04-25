from crewai import Agent, Task, Crew, Process,LLM
from langchain.tools import tool
import requests
import base64
import re
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime
from .models import GitHubProject, JobPosting, MatchResult, ScrapingLog
from django.conf import settings
from django.utils import timezone

# Initialize Gemini LLM
gemini_api_key = settings.GEMINI_API_KEY
gemini_llm = LLM(model="gemini-pro",
                  google_api_key=gemini_api_key)

class GitHubScraper:
    def __init__(self, github_token=None):
        self.github_token = github_token or settings.GITHUB_API_KEY
        self.headers = {}
        if self.github_token:
            self.headers = {'Authorization': f'token {self.github_token}'}
    
    def get_repo_info(self, repo_url):
        # Extract owner and repo name from URL
        pattern = r'github\.com/([^/]+)/([^/]+)'
        match = re.search(pattern, repo_url)
        if not match:
            self._log_scraping(repo_url, False, "Invalid GitHub URL format")
            return None
        
        owner, repo = match.groups()
        
        try:
            # Get repository information
            repo_api_url = f'https://api.github.com/repos/{owner}/{repo}'
            response = requests.get(repo_api_url, headers=self.headers)
            response.raise_for_status()
            repo_data = response.json()
            
            # Get languages
            languages_url = repo_data['languages_url']
            languages_response = requests.get(languages_url, headers=self.headers)
            languages_response.raise_for_status()
            languages = languages_response.json()
            
            # Get README content
            readme_url = f'https://api.github.com/repos/{owner}/{repo}/readme'
            readme_response = requests.get(readme_url, headers=self.headers)
            readme_content = ''
            if readme_response.status_code == 200:
                readme_data = readme_response.json()
                readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
            
            # Get file structure (top-level directories and files)
            contents_url = f'https://api.github.com/repos/{owner}/{repo}/contents'
            contents_response = requests.get(contents_url, headers=self.headers)
            contents_response.raise_for_status()
            contents_data = contents_response.json()
            
            file_structure = {}
            for item in contents_data:
                file_structure[item['name']] = {
                    'type': item['type'],
                    'size': item.get('size', 0) if item['type'] == 'file' else 0,
                    'path': item['path']
                }
            
            # Get dependencies from package.json or requirements.txt if they exist
            dependencies = {}
            package_json_url = f'https://api.github.com/repos/{owner}/{repo}/contents/package.json'
            requirements_txt_url = f'https://api.github.com/repos/{owner}/{repo}/contents/requirements.txt'
            
            # Check for package.json (Node.js)
            package_response = requests.get(package_json_url, headers=self.headers)
            if package_response.status_code == 200:
                package_data = package_response.json()
                package_content = base64.b64decode(package_data['content']).decode('utf-8')
                try:
                    package_json = json.loads(package_content)
                    dependencies['node'] = {
                        'dependencies': package_json.get('dependencies', {}),
                        'devDependencies': package_json.get('devDependencies', {})
                    }
                except json.JSONDecodeError:
                    pass
            
            # Check for requirements.txt (Python)
            req_response = requests.get(requirements_txt_url, headers=self.headers)
            if req_response.status_code == 200:
                req_data = req_response.json()
                req_content = base64.b64decode(req_data['content']).decode('utf-8')
                python_deps = {}
                for line in req_content.splitlines():
                    if line and not line.startswith('#'):
                        parts = line.split('==')
                        if len(parts) > 1:
                            python_deps[parts[0].strip()] = parts[1].strip()
                        else:
                            python_deps[line.strip()] = 'latest'
                dependencies['python'] = python_deps
            
            # Get last commit date
            commits_url = f'https://api.github.com/repos/{owner}/{repo}/commits'
            commits_response = requests.get(commits_url, headers=self.headers, params={'per_page': 1})
            commits_response.raise_for_status()
            commits_data = commits_response.json()
            last_commit = None
            if commits_data:
                last_commit_date = commits_data[0]['commit']['committer']['date']
                last_commit = datetime.strptime(last_commit_date, '%Y-%m-%dT%H:%M:%SZ')
            
            self._log_scraping(repo_url, True)
            
            return {
                'owner': owner,
                'name': repo,
                'description': repo_data.get('description', ''),
                'languages': languages,
                'topics': repo_data.get('topics', []),
                'readme_content': readme_content,
                'file_structure': file_structure,
                'dependencies': dependencies,
                'stars': repo_data.get('stargazers_count', 0),
                'forks': repo_data.get('forks_count', 0),
                'last_commit': last_commit,
                'url': repo_url
            }
        except Exception as e:
            self._log_scraping(repo_url, False, str(e))
            return None
    
    def _log_scraping(self, url, success, error_message=None):
        ScrapingLog.objects.create(
            url=url,
            success=success,
            error_message=error_message
        )

class JobScraper:
    def __init__(self, scraper_api_key=None):
        self.scraper_api_key = scraper_api_key or settings.SCRAPER_API_KEY
    
    def scrape_job_posting(self, job_url):
        try:
            # Use a scraping service or direct requests depending on the site
            if self.scraper_api_key:
                # Using a proxy service like ScraperAPI
                proxy_url = f'http://api.scraperapi.com?api_key={self.scraper_api_key}&url={job_url}'
                response = requests.get(proxy_url)
            else:
                # Direct request (may be blocked by some sites)
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(job_url, headers=headers)
            
            response.raise_for_status()
            html_content = response.text
            
            # Parse the HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract job details (this will vary based on the job board)
            job_data = self._parse_job_posting(soup, job_url)
            
            self._log_scraping(job_url, True)
            return job_data
        
        except Exception as e:
            self._log_scraping(job_url, False, str(e))
            return None
    
    def _parse_job_posting(self, soup, url):
        # This is a simplified parser that would need to be customized for each job board
        job_data = {
            'title': '',
            'company': '',
            'location': '',
            'description': '',
            'url': url,
            'source': self._get_source_from_url(url),
            'posted_date': None
        }
        
        # Extract job title (common patterns)
        title_tags = soup.select('h1, .job-title, .jobsearch-JobInfoHeader-title')
        if title_tags:
            job_data['title'] = title_tags[0].get_text().strip()
        
        # Extract company name (common patterns)
        company_tags = soup.select('.company-name, .jobsearch-InlineCompanyRating, .employer-name')
        if company_tags:
            job_data['company'] = company_tags[0].get_text().strip()
        
        # Extract location (common patterns)
        location_tags = soup.select('.location, .jobsearch-JobInfoHeader-subtitle, .job-location')
        if location_tags:
            job_data['location'] = location_tags[0].get_text().strip()
        
        # Extract job description (common patterns)
        description_tags = soup.select('.description, .jobsearch-jobDescriptionText, .job-description')
        if description_tags:
            job_data['description'] = description_tags[0].get_text().strip()
        else:
            # Fallback: get the main content area
            main_content = soup.select('main, #main-content, .main-content')
            if main_content:
                job_data['description'] = main_content[0].get_text().strip()
        
        # Extract posted date if available
        date_tags = soup.select('.posted-date, .jobsearch-JobMetadataFooter, .job-date')
        if date_tags:
            date_text = date_tags[0].get_text().strip()
            # Parse date text (would need custom logic based on format)
            # For now, just use current date
            job_data['posted_date'] = timezone.now()
        
        return job_data
    
    def _get_source_from_url(self, url):
        for board in settings.JOB_BOARDS:
            if board in url:
                return board
        return 'unknown'
    
    def _log_scraping(self, url, success, error_message=None):
        ScrapingLog.objects.create(
            url=url,
            success=success,
            error_message=error_message
        )

class CrewAIMatchingSystem:
    def __init__(self):
        self.github_scraper = GitHubScraper()
        self.job_scraper = JobScraper()
        
        # Define agents with Gemini LLM
        self.project_analyzer = Agent(
            role="GitHub Project Analyzer",
            goal="Analyze GitHub projects to extract key technologies, patterns, and skills",
            backstory="You are an expert in code analysis and software engineering patterns. You can look at a GitHub project and understand its technical stack, complexity, and the skills required to build it.",
            verbose=True,
            llm=gemini_llm
        )
        
        self.job_analyzer = Agent(
            role="Job Description Analyzer",
            goal="Extract key requirements, skills, and qualifications from job descriptions",
            backstory="You are an expert in technical recruiting and job market analysis. You can parse job descriptions to identify the core skills, technologies, and qualifications that employers are seeking.",
            verbose=True,
            llm=gemini_llm
        )
        
        self.matcher = Agent(
            role="Project-Job Matcher",
            goal="Match GitHub projects with job descriptions based on skill alignment",
            backstory="You are an AI matching specialist who can compare the skills demonstrated in GitHub projects with the requirements in job descriptions. You provide accurate matching scores and detailed explanations of the match quality.",
            verbose=True,
            llm=gemini_llm
        )
    
    @tool
    def analyze_github_project(self, repo_url):
        """Analyze a GitHub repository to extract key information"""
        # Scrape repository data
        repo_info = self.github_scraper.get_repo_info(repo_url)
        if not repo_info:
            return {"error": "Failed to retrieve repository information"}
        
        # Save to database
        project, created = GitHubProject.objects.update_or_create(
            repo_url=repo_url,
            defaults={
                'owner': repo_info['owner'],
                'name': repo_info['name'],
                'description': repo_info['description'],
                'languages': repo_info['languages'],
                'topics': repo_info['topics'],
                'readme_content': repo_info['readme_content'],
                'file_structure': repo_info['file_structure'],
                'dependencies': repo_info['dependencies'],
                'stars': repo_info['stars'],
                'forks': repo_info['forks'],
                'last_commit': repo_info['last_commit']
            }
        )
        
        # Create a task for the project analyzer agent
        task = Task(
            description=f"""
            Analyze the GitHub project at {repo_url}.
            
            Project details:
            - Owner: {repo_info['owner']}
            - Name: {repo_info['name']}
            - Description: {repo_info['description']}
            - Languages: {json.dumps(repo_info['languages'])}
            - Topics: {json.dumps(repo_info['topics'])}
            - README: {repo_info['readme_content'][:1000]}... (truncated)
            - Dependencies: {json.dumps(repo_info['dependencies'])}
            
            Extract the key technologies, frameworks, programming languages, and skills demonstrated in this project.
            Provide a detailed analysis of the project's technical stack and the skills required to work on it.
            Format your response as JSON with the following structure:
            {{
                "primary_language": "string",
                "frameworks": ["string"],
                "libraries": ["string"],
                "tools": ["string"],
                "skills": ["string"],
                "project_complexity": "low|medium|high",
                "domain": "string",
                "summary": "string"
            }}
            """,
            agent=self.project_analyzer,
            expected_output="A JSON object containing the project analysis"
        )
        
        # Execute the task
        result = task.execute()
        
        try:
            # Parse the JSON result
            analysis = json.loads(result)
            
            # Update the project with extracted skills
            project.skills = analysis.get('skills', [])
            project.save()
            
            return {
                'project_id': str(project.id),
                'analysis': analysis
            }
        except json.JSONDecodeError:
            # If the result is not valid JSON, return the raw text
            return {
                'project_id': str(project.id),
                'analysis': result
            }
    
    @tool
    def analyze_job_posting(self, job_title, job_description, job_url=None):
        """Analyze a job posting to extract key requirements and skills"""
        job_data = {
            'title': job_title,
            'description': job_description,
            'url': job_url
        }
        
        # If a URL is provided, try to scrape additional details
        if job_url:
            scraped_data = self.job_scraper.scrape_job_posting(job_url)
            if scraped_data:
                # Merge scraped data with provided data, prioritizing provided data
                for key, value in scraped_data.items():
                    if key not in job_data or not job_data[key]:
                        job_data[key] = value
        
        # Save to database
        job = JobPosting.objects.create(
            title=job_data['title'],
            company=job_data.get('company'),
            location=job_data.get('location'),
            description=job_data['description'],
            url=job_data.get('url'),
            source=job_data.get('source'),
            posted_date=job_data.get('posted_date')
        )
        
        # Create a task for the job analyzer agent
        task = Task(
            description=f"""
            Analyze the job posting titled '{job_data['title']}' from {job_data.get('company', 'Unknown Company')}.
            
            Job Description:
            {job_data['description']}
            
            Extract the key skills, technologies, frameworks, and qualifications required for this position.
            Identify both technical and soft skills mentioned in the job description.
            Determine the experience level required (entry, mid, senior).
            
            Format your response as JSON with the following structure:
            {{
                "required_skills": ["string"],
                "preferred_skills": ["string"],
                "technical_skills": ["string"],
                "soft_skills": ["string"],
                "experience_level": "entry|mid|senior",
                "education_requirements": "string",
                "job_type": "full-time|part-time|contract",
                "summary": "string"
            }}
            """,
            agent=self.job_analyzer,
            expected_output="A JSON object containing the job analysis"
        )
        
        # Execute the task
        result = task.execute()
        
        try:
            # Parse the JSON result
            analysis = json.loads(result)
            
            # Update the job with extracted skills
            job.skills_required = analysis.get('required_skills', []) + analysis.get('technical_skills', [])
            job.experience_level = analysis.get('experience_level')
            job.job_type = analysis.get('job_type')
            job.save()
            
            return {
                'job_id': str(job.id),
                'analysis': analysis
            }
        except json.JSONDecodeError:
            # If the result is not valid JSON, return the raw text
            return {
                'job_id': str(job.id),
                'analysis': result
            }
    
    @tool
    def match_project_to_jobs(self, project_id, top_n=5):
        """Match a GitHub project to relevant job postings"""
        try:
            project = GitHubProject.objects.get(id=project_id)
        except GitHubProject.DoesNotExist:
            return {"error": "Project not found"}
        
        # Get all job postings (in a real system, you'd filter by relevance first)
        jobs = JobPosting.objects.all().order_by('-created_at')[:20]  # Limit to recent jobs
        
        if not jobs:
            return {"error": "No job postings available for matching"}
        
        # Create a matching crew
        crew = Crew(
            agents=[self.project_analyzer, self.job_analyzer, self.matcher],
            tasks=[
                Task(
                    description=f"""
                    Match the GitHub project '{project.owner}/{project.name}' with relevant job postings.
                    
                    Project details:
                    - Description: {project.description}
                    - Languages: {json.dumps(project.languages)}
                    - Topics: {json.dumps(project.topics)}
                    - README excerpt: {project.readme_content[:500] if project.readme_content else 'No README available'}
                    
                    Job postings to match against:
                    {self._format_jobs_for_matching(jobs)}
                    
                    For each job, provide:
                    1. A match score (0-100)
                    2. Key matching skills between the project and job
                    3. Important skills mentioned in the job that are not evident in the project
                    4. A detailed explanation of why the match score was assigned
                    
                    Format your response as JSON with the following structure:
                    {{
                        "matches": [
                            {{
                                "job_id": "string",
                                "match_score": number,
                                "key_matches": ["string"],
                                "missing_skills": ["string"],
                                "explanation": "string"
                            }}
                        ]
                    }}
                    
                    Sort the matches by match_score in descending order.
                    """,
                    agent=self.matcher,
                    expected_output="A JSON object containing job matches with scores and explanations"
                )
            ],
            verbose=True,
            process=Process.sequential
        )
        
        # Execute the crew
        result = crew.kickoff()
        
        # Process and save matches
        matches = self._process_match_results(result, project, jobs, 'project_to_job')
        
        return {
            'project': f"{project.owner}/{project.name}",
            'matches': matches
        }
    
    @tool
    def match_job_to_projects(self, job_id, top_n=5):
        """Match a job posting to relevant GitHub projects"""
        try:
            job = JobPosting.objects.get(id=job_id)
        except JobPosting.DoesNotExist:
            return {"error": "Job not found"}
        
        # Get all projects (in a real system, you'd filter by relevance first)
        projects = GitHubProject.objects.all().order_by('-created_at')[:20]  # Limit to recent projects
        
        if not projects:
            return {"error": "No projects available for matching"}
        
        # Create a matching crew
        crew = Crew(
            agents=[self.project_analyzer, self.job_analyzer, self.matcher],
            tasks=[
                Task(
                    description=f"""
                    Match the job posting '{job.title}' from {job.company or 'Unknown Company'} with relevant GitHub projects.
                    
                    Job details:
                    - Title: {job.title}
                    - Company: {job.company or 'Unknown'}
                    - Description: {job.description[:1000]}... (truncated)
                    
                    GitHub projects to match against:
                    {self._format_projects_for_matching(projects)}
                    
                    For each project, provide:
                    1. A match score (0-100)
                    2. Key matching skills between the job and project
                    3. Important skills mentioned in the job that are not evident in the project
                    4. A detailed explanation of why the match score was assigned
                    
                    Format your response as JSON with the following structure:
                    {{
                        "matches": [
                            {{
                                "project_id": "string",
                                "match_score": number,
                                "key_matches": ["string"],
                                "missing_skills": ["string"],
                                "explanation": "string"
                            }}
                        ]
                    }}
                    
                    Sort the matches by match_score in descending order.
                    """,
                    agent=self.matcher,
                    expected_output="A JSON object containing project matches with scores and explanations"
                )
            ],
            verbose=True,
            process=Process.sequential
        )
        
        # Execute the crew
        result = crew.kickoff()
        
        # Process and save matches
        matches = self._process_match_results(result, job, projects, 'job_to_project')
        
        return {
            'job': job.title,
            'matches': matches
        }
    
    def _format_jobs_for_matching(self, jobs):
        """Format job postings for the matching task"""
        job_texts = []
        for job in jobs:
            job_text = f"""
            Job ID: {job.id}
            Title: {job.title}
            Company: {job.company or 'Unknown'}
            Description: {job.description[:500]}... (truncated)
            """
            job_texts.append(job_text)
        
        return "\n\n".join(job_texts)
    
    def _format_projects_for_matching(self, projects):
        """Format GitHub projects for the matching task"""
        project_texts = []
        for project in projects:
            project_text = f"""
            Project ID: {project.id}
            Name: {project.owner}/{project.name}
            Description: {project.description or 'No description available'}
            Languages: {json.dumps(project.languages)}
            Topics: {json.dumps(project.topics)}
            """
            project_texts.append(project_text)
        
        return "\n\n".join(project_texts)
    
    def _process_match_results(self, result, source, targets, match_type):
        """Process and save match results"""
        try:
            # Try to parse the result as JSON
            match_data = json.loads(result)
            matches = match_data.get('matches', [])
        except json.JSONDecodeError:
            # If parsing fails, return an error
            return [{"error": "Failed to parse matching results"}]
        
        saved_matches = []
        
        for match in matches:
            try:
                if match_type == 'project_to_job':
                    project = source
                    job_id = match.get('job_id')
                    job = next((j for j in targets if str(j.id) == job_id), None)
                    
                    if not job:
                        continue
                else:  # job_to_project
                    job = source
                    project_id = match.get('project_id')
                    project = next((p for p in targets if str(p.id) == project_id), None)
                    
                    if not project:
                        continue
                
                # Create or update match result
                match_result, created = MatchResult.objects.update_or_create(
                    project=project,
                    job=job,
                    defaults={
                        'match_type': match_type,
                        'match_score': match.get('match_score', 0),
                        'key_matches': match.get('key_matches', []),
                        'missing_skills': match.get('missing_skills', []),
                        'explanation': match.get('explanation', '')
                    }
                )
                
                saved_matches.append({
                    'id': str(match_result.id),
                    'type': 'job' if match_type == 'project_to_job' else 'project',
                    'title': job.title if match_type == 'project_to_job' else f"{project.owner}/{project.name}",
                    'company': job.company if match_type == 'project_to_job' else None,
                    'owner': project.owner if match_type == 'job_to_project' else None,
                    'matchScore': match_result.match_score,
                    'keyMatches': match_result.key_matches,
                    'missingSkills': match_result.missing_skills,
                    'description': (job.description[:200] + '...') if match_type == 'project_to_job' else (project.description[:200] + '...') if project.description else 'No description available',
                    'url': job.url if match_type == 'project_to_job' else project.repo_url,
                    'explanation': match_result.explanation
                })
            except Exception as e:
                # Log the error but continue processing other matches
                print(f"Error processing match: {str(e)}")
        
        return saved_matches
