from django.db import models
from django.db.models.deletion import CASCADE
from django.db.models.query import prefetch_related_objects
from Employee.models import CustomEmployeeDetails
from projects.models import Projects ,Task

from django.utils import timezone
# Create your models here.
# class employeedetails(models.Model):
#     name = models.CharField(max_length=100,null=False,default=None)
#     eid=models.IntegerField(null=False,default=None)

class timesheet_submission(models.Model):
    uid = models.ForeignKey(CustomEmployeeDetails,on_delete=CASCADE,default=None)
    submission_status = models.CharField(max_length=50,default=None,null=True)
    task_id = models.ForeignKey(Task,on_delete=CASCADE,default = None)
    # name=models.CharField(max_length=50,default=None)
    # eid=models.IntegerField(default=None)
    # project_name=models.CharField(max_length=100,default=None)
    # project_id = models.ForeignKey(Projects,on_delete=CASCADE)
    # milestone = models.CharField(max_length=100,default=None)
    date= models.DateField(null=False,default=timezone.now)
    # task=models.CharField(max_length=250,default=None,null=True)
    hours=models.IntegerField(default=None)
    # location =models.CharField(null=False,default=None,max_length=25)
    comment=models.CharField(max_length=1500,default=None,null=False)
    submission_date= models.DateField(null=False,default=timezone.now)
    created_date = models.DateTimeField(auto_now_add=True)
    
class submission(models.Model):
    uid = models.ForeignKey(CustomEmployeeDetails,on_delete=CASCADE)
    date = models.DateField(default=None)
    hours=models.IntegerField(default=None)
    comment=models.CharField(max_length=1500,default=None,null=False)
    created_date = models.DateTimeField(auto_now_add=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    submission_status = models.CharField(max_length=50,default=None,null=True)
    tid = models.ForeignKey(Task,on_delete=CASCADE)
    pid = models.ForeignKey(Projects,on_delete=CASCADE)  