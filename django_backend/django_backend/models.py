from django.db import models

class GitHubProject(models.Model):
    repo_url = models.URLField(max_length=255)
    owner = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    languages = models.JSONField(default=dict)
    topics = models.JSONField(default=list)
    readme_content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.owner}/{self.name}"

class JobPosting(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    skills_required = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.company or 'Unknown'}"

class MatchResult(models.Model):
    MATCH_TYPES = (
        ('project_to_job', 'Project to Job'),
        ('job_to_project', 'Job to Project'),
    )
    
    match_type = models.CharField(max_length=20, choices=MATCH_TYPES)
    project = models.ForeignKey(GitHubProject, on_delete=models.CASCADE, null=True, blank=True)
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, null=True, blank=True)
    match_score = models.FloatField()
    key_matches = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.match_type == 'project_to_job':
            return f"Project {self.project} to Job {self.job} - {self.match_score}%"
        return f"Job {self.job} to Project {self.project} - {self.match_score}%"
