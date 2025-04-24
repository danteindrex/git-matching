from django.db import models
from django.utils import timezone
import uuid

class GitHubProject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repo_url = models.URLField(max_length=255, unique=True)
    owner = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    languages = models.JSONField(default=dict)
    topics = models.JSONField(default=list)
    readme_content = models.TextField(blank=True, null=True)
    file_structure = models.JSONField(default=dict)
    dependencies = models.JSONField(default=dict)
    stars = models.IntegerField(default=0)
    forks = models.IntegerField(default=0)
    last_commit = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.owner}/{self.name}"
    
    class Meta:
        indexes = [
            models.Index(fields=['owner', 'name']),
        ]

class JobPosting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    url = models.URLField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)
    skills_required = models.JSONField(default=list)
    experience_level = models.CharField(max_length=50, blank=True, null=True)
    job_type = models.CharField(max_length=50, blank=True, null=True)
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    posted_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.company or 'Unknown'}"
    
    class Meta:
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['company']),
        ]

class MatchResult(models.Model):
    MATCH_TYPES = (
        ('project_to_job', 'Project to Job'),
        ('job_to_project', 'Job to Project'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match_type = models.CharField(max_length=20, choices=MATCH_TYPES)
    project = models.ForeignKey(GitHubProject, on_delete=models.CASCADE, related_name='matches')
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='matches')
    match_score = models.FloatField()
    key_matches = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.match_type == 'project_to_job':
            return f"Project {self.project} to Job {self.job} - {self.match_score}%"
        return f"Job {self.job} to Project {self.project} - {self.match_score}%"
    
    class Meta:
        indexes = [
            models.Index(fields=['match_type']),
            models.Index(fields=['match_score']),
            models.Index(fields=['created_at']),
        ]
        unique_together = ('project', 'job')

class ScrapingLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(max_length=255)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.url} - {'Success' if self.success else 'Failed'}"
