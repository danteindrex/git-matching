from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import GitHubProject, JobPosting, MatchResult
from .crew_ai_agents import CrewAIMatchingSystem

# Initialize the CrewAI matching system
matching_system = CrewAIMatchingSystem()

@csrf_exempt
@require_http_methods(["POST"])
def analyze_github_project(request):
    try:
        data = json.loads(request.body)
        repo_url = data.get('repo_url')
        
        if not repo_url:
            return JsonResponse({'error': 'Repository URL is required'}, status=400)
        
        result = matching_system.analyze_github_project(repo_url)
        return JsonResponse({'success': True, 'result': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def analyze_job_posting(request):
    try:
        data = json.loads(request.body)
        job_title = data.get('job_title')
        job_description = data.get('job_description')
        
        if not job_title or not job_description:
            return JsonResponse({'error': 'Job title and description are required'}, status=400)
        
        result = matching_system.analyze_job_posting(job_title, job_description)
        return JsonResponse({'success': True, 'result': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def match_project_to_jobs(request):
    try:
        data = json.loads(request.body)
        project_id = data.get('project_id')
        
        if not project_id:
            return JsonResponse({'error': 'Project ID is required'}, status=400)
        
        result = matching_system.match_project_to_jobs(project_id)
        return JsonResponse({'success': True, 'result': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def match_job_to_projects(request):
    try:
        data = json.loads(request.body)
        job_id = data.get('job_id')
        
        if not job_id:
            return JsonResponse({'error': 'Job ID is required'}, status=400)
        
        result = matching_system.match_job_to_projects(job_id)
        return JsonResponse({'success': True, 'result': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_match_results(request, match_id=None):
    if match_id:
        try:
            match = MatchResult.objects.get(id=match_id)
            return JsonResponse({
                'id': match.id,
                'match_type': match.match_type,
                'project': f"{match.project.owner}/{match.project.name}" if match.project else None,
                'job': match.job.title if match.job else None,
                'match_score': match.match_score,
                'key_matches': match.key_matches,
                'missing_skills': match.missing_skills,
                'explanation': match.explanation,
                'created_at': match.created_at.isoformat()
            })
        except MatchResult.DoesNotExist:
            return JsonResponse({'error': 'Match result not found'}, status=404)
    else:
        matches = MatchResult.objects.all().order_by('-created_at')[:20]
        results = []
        
        for match in matches:
            results.append({
                'id': match.id,
                'match_type': match.match_type,
                'project': f"{match.project.owner}/{match.project.name}" if match.project else None,
                'job': match.job.title if match.job else None,
                'match_score': match.match_score,
                'created_at': match.created_at.isoformat()
            })
        
        return JsonResponse({'results': results})
