from django.shortcuts import render, redirect
from .forms import ProjectForm, JobForm

def index(request):
    return render(request, "matcher_ui/index.html")

def submit_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            # TODO: Process the project form and get results
            # dummy data for now:
            results = []
            return render(request, "matcher_ui/match_results.html", {"results": results, "type": "project"})
    else:
        form = ProjectForm()
    return render(request, "matcher_ui/project_form.html", {"form": form})

def submit_job(request):
    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            # TODO: Process the job form and get results
            # dummy data for now:
            results = []
            return render(request, "matcher_ui/match_results.html", {"results": results, "type": "job"})
    else:
        form = JobForm()
    return render(request, "matcher_ui/job_form.html", {"form": form})

def match_results(request):
    # You can implement persistent state or pass results through context/session
    return render(request, "matcher_ui/match_results.html", {})