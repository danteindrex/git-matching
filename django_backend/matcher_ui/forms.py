from django import forms

class ProjectForm(forms.Form):
    repo_url = forms.URLField(label="GitHub Repository URL", required=True, widget=forms.URLInput(attrs={'class': 'form-control'}))
    additional_info = forms.CharField(label="Additional Information", required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}))

class JobForm(forms.Form):
    job_title = forms.CharField(label="Job Title", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    job_url = forms.URLField(label="Job Posting URL", required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    job_description = forms.CharField(label="Job Description", required=True, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 8}))