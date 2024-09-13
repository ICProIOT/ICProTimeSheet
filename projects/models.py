from django.db import models
from django.db.models.query import QuerySet
from  django.utils import timezone
from django.db.models.deletion import CASCADE
from numpy import mod
from Employee.models import CustomEmployeeDetails
from file_management.storage import OverwriteStorage


# Create your models here.
class ChecklistManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class Projects(models.Model):  # Name change needed
    # pid = models.IntegerField(unique=True,default="",null=False)
    p_code = models.CharField(max_length=25,blank=True)
    name = models.CharField(max_length=100,default="",null=False)
    department = models.CharField(max_length=30,default="",null=False)
    checklists = models.ManyToManyField("Checklist", blank=True, default=[])
    # weightage = models.IntegerField(default=0,null=False)
    is_active = models.BooleanField(default=True)
    # estimated_hrs = models.IntegerField(default=None,null=True)
    updated_date = models.DateTimeField(auto_now=True)
    # quotted_hours = models.IntegerField(default=0,null=False)
    uid = models.ManyToManyField(CustomEmployeeDetails)

class Milestone(models.Model):
    name = models.CharField(max_length=1000,default="",null=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    weightage = models.IntegerField(default=0,null=False)
    pid = models.ForeignKey(Projects,on_delete=CASCADE)

class Task(models.Model):
    name = models.CharField(max_length=1000,default="",null=False)
    start_date = models.DateField(default=timezone.now,null=False)
    end_date = models.DateField(default=timezone.now,null=False)
    weightage = models.IntegerField(default=0,null=False)
    priority = models.CharField(max_length=30,default="",null=False)
    assigned_to = models.CharField(max_length=30,default="",null=False)
    status = models.CharField(max_length=30,default="",null=False)
    # estimated_hrs = models.IntegerField(default=0,null=False)
    description = models.CharField(max_length=1000,default="",null=False)
    assigned_by = models.CharField(max_length=100,default=None,null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    mid = models.ForeignKey(Milestone,on_delete=CASCADE)
    pid = models.ForeignKey(Projects,on_delete=CASCADE)
    quotted_hours = models.IntegerField(default=0,null=False)

# Rev1.2 
# Creating Templates for Task and Milestone
class Milestone_templates(models.Model):
    department = models.CharField(max_length=1024,default="",null=False)
    milestone = models.CharField(max_length=1024,default="",null=False)

class Task_templates(models.Model):
    task = models.CharField(max_length=1024,default="",null=False)
    mid = models.ForeignKey(Milestone_templates,on_delete=CASCADE)


# Rev.3
# class project_user(models.Model):
#     pid = models.ManyToManyField(Projects)
#     uid = models.ForeignKey(CustomEmployeeDetails,on_delete=models.DO_NOTHING,default=None)






#
# Creating checklist models for project
#

# Checklist model
class Checklist(models.Model):
    name = models.CharField(default="", max_length=1024,null=False)
    remarks = models.TextField(default="", null=False)
    section = models.ManyToManyField("Section", blank=True)
    is_deleted = models.BooleanField(default=False)
    objects = ChecklistManager()
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()
        return 1,{"Checklist":1}
    
    def __str__(self):
        return self.name

# Section model
class Section(models.Model):
    name = models.CharField(default="", max_length=50,null=True)
    question = models.ManyToManyField("Question", blank=True)
    is_deleted = models.BooleanField(default=False)
    objects = ChecklistManager()

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()
        return 1,{"Section":1}
    
    def __str__(self):
        return self.name

# Question model
class Question(models.Model):
    QUESTION_TYPE = (("radio","Radio Button"),
                     ("text","Text Field"))

    question = models.CharField(default="", max_length=1024,null=False)
    type = models.CharField(default="text", max_length=50,null=False, choices=QUESTION_TYPE)
    options = models.ManyToManyField("QuestionOption",blank=True) 
    attachment = models.FileField(storage=OverwriteStorage(), upload_to='checklist_questions/', null=True, blank=True, default=None)
    is_deleted = models.BooleanField(default=False)
    objects = ChecklistManager()
    def delete(self, *args,**kwargs) :
        self.attachment.delete()
        self.is_deleted = True
        self.save()
        return 1,{"Question":1}
    
    def __str__(self):
        return self.question

class QuestionOption(models.Model):
    option = models.CharField(max_length=1024,default="",null=False)
    is_deleted = models.BooleanField(default=False)
    objects = ChecklistManager()

    def delete(self, *args,**kwargs) :
        self.is_deleted = True
        self.save()
        return 1,{"QuestionOption":1}
    
    def __str__(self):
        return self.option

class Answer(models.Model):
    text = models.TextField(default="",null=True)
    remarks = models.TextField(default="",null=True,blank=True)
    checklist = models.ForeignKey('Checklist', on_delete=models.DO_NOTHING, default='', blank=True)
    section = models.ForeignKey('Section', on_delete=models.DO_NOTHING, default='', blank=True)
    question = models.ForeignKey('Question', on_delete=models.DO_NOTHING, default='', blank=True)
    project = models.ForeignKey('Projects',on_delete=models.DO_NOTHING, default='', blank=True)
    is_deleted = models.BooleanField(default=False)
    objects = ChecklistManager()
    class Meta:
        unique_together = ('question', 'checklist', 'section')

    def delete(self, *args,**kwargs) :
        self.is_deleted = True
        self.save()
        return 1,{"Answer":1}
    
    def __str__(self):
        return str(self.text)