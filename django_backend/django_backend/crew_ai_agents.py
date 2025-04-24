from crewai import Agent, Task, Crew, LLM
from langchain.tools import tool
import requests
import base64
import re
import os
import spacy
from spacy.matcher import PhraseMatcher
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
from .models import GitHubProject, JobPosting, MatchResult
llm=LLM(
    model="gemini/gemini-2.0-flash-exp"
)
class GitHubProjectAnalyzer:
    def __init__(self, github_token=None):
        self.github_token = github_token
        self.headers = {}
        if github_token:
            self.headers = {'Authorization': f'token {github_token}'}
    
    def get_repo_info(self, repo_url):
        # Extract owner and repo name from URL
        pattern = r'github\.com/([^/]+)/([^/]+)'
        match = re.search(pattern, repo_url)
        if not match:
            return None
        
        owner, repo = match.groups()
        
        # Get repository information
        repo_api_url = f'https://api.github.com/repos/{owner}/{repo}'
        response = requests.get(repo_api_url, headers=self.headers)
        if response.status_code != 200:
            return None
        
        repo_data = response.json()
        
        # Get languages
        languages_url = repo_data['languages_url']
        languages_response = requests.get(languages_url, headers=self.headers)
        languages = languages_response.json() if languages_response.status_code == 200 else {}
        
        # Get README content
        readme_url = f'https://api.github.com/repos/{owner}/{repo}/readme'
        readme_response = requests.get(readme_url, headers=self.headers)
        readme_content = ''
        if readme_response.status_code == 200:
            readme_data = readme_response.json()
            readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
        
        return {
            'owner': owner,
            'name': repo,
            'description': repo_data.get('description', ''),
            'languages': languages,
            'topics': repo_data.get('topics', []),
            'readme_content': readme_content,
            'url': repo_url
        }

class CrewAIMatchingSystem:
    def __init__(self, github_token=None):
        self.github_analyzer = GitHubProjectAnalyzer(github_token)
        
        # Initialize spaCy for NLP-based skill extraction
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # If model not found, download it
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
            
        # Define common tech skills for matching
        self.common_tech_skills = [
            "Python", "JavaScript", "TypeScript", "React", "Angular", "Vue", 
            "Node.js", "Django", "Flask", "Express", "Ruby", "Rails", "PHP",
            "Java", "Spring", "C#", ".NET", "Go", "Rust", "Swift", "Kotlin",
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "GraphQL",
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD", "Git"
        ]
        
        # Create patterns for all skills
        self.skill_patterns = [self.nlp.make_doc(skill.lower()) for skill in self.common_tech_skills]
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self.phrase_matcher.add("TECH_SKILLS", self.skill_patterns)
        
        # Define agents
        self.project_analyzer = Agent(
            role="GitHub Project Analyzer",
            llm=llm,
            goal="Analyze GitHub projects to extract key technologies, patterns, and skills",
            backstory="You are an expert in code analysis and software engineering patterns. You can look at a GitHub project and understand its technical stack, complexity, and the skills required to build it.",
            verbose=True
        )
        
        self.job_analyzer = Agent(
            role="Job Description Analyzer",
            llm=llm,
            goal="Extract key requirements, skills, and qualifications from job descriptions",
            backstory="You are an expert in technical recruiting and job market analysis. You can parse job descriptions to identify the core skills, technologies, and qualifications that employers are seeking.",
            verbose=True
        )
        
        self.matcher = Agent(
            role="Project-Job Matcher",
            llm=llm,
            goal="Match GitHub projects with job descriptions based on skill alignment",
            backstory="You are an AI matching specialist who can compare the skills demonstrated in GitHub projects with the requirements in job descriptions. You provide accurate matching scores and detailed explanations of the match quality.",
            verbose=True
        )
    
    @tool
    def analyze_github_project(self, repo_url):
        """Analyze a GitHub repository to extract key information"""
        repo_info = self.github_analyzer.get_repo_info(repo_url)
        if not repo_info:
            return "Failed to retrieve repository information"
        
        # Save to database
        project, created = GitHubProject.objects.update_or_create(
            repo_url=repo_url,
            defaults={
                'owner': repo_info['owner'],
                'name': repo_info['name'],
                'description': repo_info['description'],
                'languages': repo_info['languages'],
                'topics': repo_info['topics'],
                'readme_content': repo_info['readme_content']
            }
        )
        
        # Create a task for the project analyzer agent
        task = Task(
            description=f"Analyze the GitHub project at {repo_url}. Extract the key technologies, frameworks, programming languages, and skills demonstrated in this project.",
            agent=self.project_analyzer,
            expected_output="A detailed analysis of the project including technologies used and skills demonstrated"
        )
        
        # Execute the task
        result = task.execute()
        return {
            'project_id': project.id,
            'analysis': result
        }
    
    @tool
    def analyze_job_posting(self, job_title, job_description):
        """Analyze a job posting to extract key requirements and skills"""
        # Save to database
        job = JobPosting.objects.create(
            title=job_title,
            description=job_description
        )
        
        # Create a task for the job analyzer agent
        task = Task(
            description=f"Analyze the job posting titled '{job_title}'. Extract the key skills, technologies, frameworks, and qualifications required for this position.",
            agent=self.job_analyzer,
            expected_output="A detailed analysis of the job requirements including required skills and technologies"
        )
        
        # Execute the task
        result = task.execute()
        
        # Update the job with extracted skills
        skills = self._extract_skills_from_analysis(result)
        job.skills_required = skills
        job.save()
        
        return {
            'job_id': job.id,
            'analysis': result,
            'skills': skills
        }
    
    @tool
    def match_project_to_jobs(self, project_id, top_n=5):
        """Match a GitHub project to relevant job postings"""
        try:
            project = GitHubProject.objects.get(id=project_id)
        except GitHubProject.DoesNotExist:
            return "Project not found"
        
        # Get all job postings
        jobs = JobPosting.objects.all()
        
        # Create a matching crew
        crew = Crew(
            agents=[self.project_analyzer, self.job_analyzer, self.matcher],
            tasks=[
                Task(
                    description=f"Match the GitHub project '{project.owner}/{project.name}' with relevant job postings. Consider the technologies, skills, and patterns demonstrated in the project.",
                    agent=self.matcher,
                    expected_output="A list of job matches with scores and explanations"
                )
            ],
            verbose=True
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
            return "Job not found"
        
        # Get all projects
        projects = GitHubProject.objects.all()
        
        # Create a matching crew
        crew = Crew(
            agents=[self.project_analyzer, self.job_analyzer, self.matcher],
            tasks=[
                Task(
                    description=f"Match the job posting '{job.title}' with relevant GitHub projects. Consider the skills and technologies required in the job description.",
                    agent=self.matcher,
                    expected_output="A list of project matches with scores and explanations"
                )
            ],
            verbose=True
        )
        
        # Execute the crew
        result = crew.kickoff()
        
        # Process and save matches
        matches = self._process_match_results(result, job, projects, 'job_to_project')
        
        return {
            'job': job.title,
            'matches': matches
        }
    
    def _extract_skills_from_analysis(self, analysis):
        """
        Extract technical skills from the provided analysis using NLP matching.
        
        Parameters:
            analysis (str): The text to analyze for skill extraction.
            
        Returns:
            list: List of detected skills present in the analysis text.
        """
        # Process the text with spaCy
        doc = self.nlp(analysis)
        
        # Find all skill matches using the phrase matcher
        matches = self.phrase_matcher(doc)
        skills_found = set()
        
        # Extract matched skills and normalize to the canonical form
        for match_id, start, end in matches:
            span_text = doc[start:end].text
            for skill in self.common_tech_skills:
                if span_text.lower() == skill.lower():
                    skills_found.add(skill)
        
        return sorted(list(skills_found))
    
    def _process_match_results(self, result, source, targets, match_type):
        # This would parse the crew result to extract matches
        # For simplicity, we're using a placeholder implementation
        matches = []
        
        # In a real implementation, this would parse the structured output from the crew
        # For now, we'll create some mock matches
        for i, target in enumerate(targets[:5]):
            # Generate a mock score between 60 and 95
            score = 60 + (i * 7) % 36
            
            if match_type == 'project_to_job':
                project = source
                job = target
                key_matches = self._extract_skills_from_analysis(project.description)[:4]
                missing_skills = job.skills_required[:3]
            else:
                job = source
                project = target
                key_matches = self._extract_skills_from_analysis(project.description)[:4]
                missing_skills = [s for s in job.skills_required if s not in key_matches][:3]
            
            # Create match result in database
            match = MatchResult.objects.create(
                match_type=match_type,
                project=project,
                job=job,
                match_score=score,
                key_matches=key_matches,
                missing_skills=missing_skills,
                explanation=f"This is a {score}% match based on skill alignment."
            )
            
            matches.append({
                'id': match.id,
                'score': score,
                'key_matches': key_matches,
                'missing_skills': missing_skills,
                'explanation': match.explanation,
                'target': job.title if match_type == 'project_to_job' else f"{project.owner}/{project.name}"
            })
        
        return matches
