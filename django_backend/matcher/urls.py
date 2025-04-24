from django.urls import path
from . import views

urlpatterns = [
    path('api/analyze/project', views.analyze_github_project, name='analyze_github_project'),
    path('api/analyze/job', views.analyze_job_posting, name='analyze_job_posting'),
    path('api/match/project-to-jobs', views.match_project_to_jobs, name='match_project_to_jobs'),
    path('api/match/job-to-projects', views.match_job_to_projects, name='match_job_to_projects'),
    path('api/matches', views.get_match_results, name='get_matches'),
    path('api/matches/<uuid:match_id>', views.get_match_results, name='get_match_detail'),
]
