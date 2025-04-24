from django.urls import path
from . import views
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('api/analyze/project', views.analyze_github_project, name='analyze_github_project'),
    path('api/analyze/job', views.analyze_job_posting, name='analyze_job_posting'),
    path('api/match/project-to-jobs', views.match_project_to_jobs, name='match_project_to_jobs'),
    path('api/match/job-to-projects', views.match_job_to_projects, name='match_job_to_projects'),
    path('api/matches', views.get_match_results, name='get_matches'),
    path('api/matches/<int:match_id>', views.get_match_results, name='get_match_detail'),
    path("admin/", admin.site.urls),
    path("ui/", include("matcher_ui.urls"))

]
