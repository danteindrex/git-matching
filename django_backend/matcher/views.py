from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import uuid
from .models import GitHubProject, JobPosting, MatchResult
from .crew_ai_agents import CrewAIMatchingSystem
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Initialize the CrewAI matching system
matching_system = CrewAIMatchingSystem()

@api_view(['POST'])
def analyze_github_project(request):
    """API endpoint to analyze a GitHub repository"""
    try:
        repo_url = request.data.get('repo_url')
        
        if not repo_url:
            return Response({'error': 'Repository URL is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        result = matching_system.analyze_github_project(repo_url)
        
        if 'error' in result:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'success': True, 'result': result})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def analyze_job_posting(request):
    """API endpoint to analyze a job posting"""
    try:
        job_title = request.data.get('job_title')
        job_description = request.data.get('job_description')
        job_url = request.data.get('job_url')
        
        if not job_title or not job_description:
            return Response({'error': 'Job title and description are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        result = matching_system.analyze_job_posting(job_title, job_description, job_url)
        
        if 'error' in result:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'success': True, 'result': result})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def match_project_to_jobs(request):
    """API endpoint to match a GitHub project to job postings"""
    try:
        repo_url = request.data.get('repo_url')
        
        if not repo_url:
            return Response({'error': 'Repository URL is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # First analyze the project
        project_result = matching_system.analyze_github_project(repo_url)
        
        if 'error' in project_result:
            return Response({'error': project_result['error']}, status=status.HTTP_400_BAD_REQUEST)
        
        # Then match it to jobs
        project_id = project_result['project_id']
        match_result = matching_system.match_project_to_jobs(project_id)
        
        if 'error' in match_result:
            return Response({'error': match_result['error']}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'success': True, 'matches': match_result['matches']})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def match_job_to_projects(request):
    """API endpoint to match a job posting to GitHub projects"""
    try:
        job_title = request.data.get('job_title')
        job_description = request.data.get('job_description')
        job_url = request.data.get('job_url')
        
        if not job_title or not job_description:
            return Response({'error': 'Job title and description are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # First analyze the job
        job_result = matching_system.analyze_job_posting(job_title, job_description, job_url)
        
        if 'error' in job_result:
            return Response({'error': job_result['error']}, status=status.HTTP_400_BAD_REQUEST)
        
        # Then match it to projects
        job_id = job_result['job_id']
        match_result = matching_system.match_job_to_projects(job_id)
        
        if 'error' in match_result:
            return Response({'error': match_result['error']}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'success': True, 'matches': match_result['matches']})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_match_results(request, match_id=None):
    """API endpoint to get match results"""
    try:
        if match_id:
            try:
                match = MatchResult.objects.get(id=match_id)
                return Response({
                    'id': str(match.id),
                    'match_type': match.match_type,
                    'project': {
                        'id': str(match.project.id),
                        'owner': match.project.owner,
                        'name': match.project.name,
                        'url': match.project.repo_url
                    },
                    'job': {
                        'id': str(match.job.id),
                        'title': match.job.title,
                        'company': match.job.company,
                        'url': match.job.url
                    },
                    'match_score': match.match_score,
                    'key_matches': match.key_matches,
                    'missing_skills': match.missing_skills,
                    'explanation': match.explanation,
                    'created_at': match.created_at.isoformat()
                })
            except MatchResult.DoesNotExist:
                return Response({'error': 'Match result not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            matches = MatchResult.objects.all().order_by('-created_at')[:20]
            results = []
            
            for match in matches:
                result_type = 'job' if match.match_type == 'project_to_job' else 'project'
                
                results.append({
                    'id': str(match.id),
                    'type': result_type,
                    'title': match.job.title if result_type == 'job' else f"{match.project.owner}/{match.project.name}",
                    'company': match.job.company if result_type == 'job' else None,
                    'owner': match.project.owner if result_type == 'project' else None,
                    'matchScore': match.match_score,
                    'keyMatches': match.key_matches,
                    'missingSkills': match.missing_skills,
                    'description': (match.job.description[:200] + '...') if result_type == 'job' else (match.project.description[:200] + '...') if match.project.description else 'No description available',
                    'url': match.job.url if result_type == 'job' else match.project.repo_url,
                    'explanation': match.explanation
                })
            
            return Response({'results': results})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
