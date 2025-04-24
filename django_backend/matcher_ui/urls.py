from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="matcher_ui_index"),
    path('project/', views.submit_project, name="matcher_ui_project"),
    path('job/', views.submit_job, name="matcher_ui_job"),
    path('results/', views.match_results, name="matcher_ui_results"),
]