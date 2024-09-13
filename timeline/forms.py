import datetime
from typing import ClassVar
import django
from django import forms
from django.core import validators
from django.db import models
from django.db.models.enums import Choices
from django.forms import fields, widgets
from django import forms
from django.utils.regex_helper import Choice
from .models import timesheet_submission
from django.core.validators import RegexValidator

from django.utils import timezone

class timesheet_form(forms.ModelForm):
    def clean_date(self):
        date = self.cleaned_data['date']
        thirtyfirst = timezone.now() + datetime.timedelta(days=-30)
        if date < thirtyfirst.date():
            raise forms.ValidationError("Only last 30 days are valid")    
        return date
        # date=forms.DateField(initial= timezone.now)

    # eid = forms.IntegerField(initial=0)
    # name = forms.CharField(initial="")
    project_name=forms.CharField(initial="")    #(('project1','project1'),('project2','project2'),('project3','project3')) 
    task=forms.CharField(initial="")            #(('task1','task1'),('task1','task1'),('task1','task1'))
    hours=forms.IntegerField(initial=0)
    location=forms.CharField(initial="")
    
    comment=forms.CharField(initial="")

    class Meta:
       model=timesheet_submission 
       fields=['project_name','location','date','task','hours','comment']   #'eid','name',



