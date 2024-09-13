from django import forms
from django.db import models
from django.db.models import fields
from django.db.models.base import Model
from .models import Projects,Milestone,Task,Milestone_templates,Task_templates, Checklist,Section,Question


class ProjectForm(forms.ModelForm):

    class Meta:
        model = Projects
        fields = ['p_code','name','department','is_active']
        readonly_fields=['checklists']

class ProjectChecklistForm(forms.ModelForm):
    class Meta:
        model = Projects
        fields = ['checklists','name']

class MilestoneForm(forms.ModelForm):
    weightage = forms.CharField(required=False)
    pid = forms.IntegerField(required=False)
    class Meta:
        model = Milestone
        fields = ['name','weightage','pid']

class TaskForm(forms.ModelForm):
    pid = forms.IntegerField(required=False)
    mid = forms.IntegerField(required=False)
    class Meta:
        model = Task
        fields = ['name','start_date','end_date','priority','assigned_to','status','description','weightage','pid','mid']

class templates_milestone_form(forms.ModelForm):
    class Meta:
        model = Milestone_templates
        fields =['milestone','department']

class templates_task_form(forms.ModelForm):
    class Meta:
        model = Task_templates
        fields =['mid','task']

class ChecklistForm(forms.ModelForm):

    class Meta:
        model = Checklist
        fields = ['name','remarks']

class SelectionForm(forms.Form):         
    selections = forms.ModelMultipleChoiceField(
        queryset=Section.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )
class QuestionForm(forms.Form):         
    question = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )