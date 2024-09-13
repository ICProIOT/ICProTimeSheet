from django.contrib import messages
from django.db.models.aggregates import Count
from django.http.response import HttpResponse, JsonResponse
from django.contrib.auth.models import Group, User,auth
from django.shortcuts import render,redirect
from .forms import (MilestoneForm, ProjectForm, 
                    templates_milestone_form,templates_task_form, 
                   SelectionForm)
from .models import Projects,Milestone,Task,Milestone_templates,Task_templates,Checklist,Section,QuestionOption
from django.db.models import F, Func, Value, CharField,Sum
from Employee.models import CustomEmployeeDetails
from django.db.models import CharField, Value as V
from django.db.models.functions import Concat
from Employee.decorators import unathenticated,allowedGroups
from django.contrib.auth.decorators import login_required
import datetime
import random
import json,pandas as pd
from django.db.models import Q,When, F,IntegerField,Sum,Func,Value,CharField
from timeline.models import timesheet_submission
from django.utils import timezone
from django.db.models import Count
from django.db.models import CharField, Case, Value, When

from projects.models import Checklist, Section, Question, Answer
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.db import transaction  
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt,csrf_protect #Add this
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from timeline import views as timeline_views
from django.views.decorators.cache import cache_control


# Create Project
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def createProject(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, 'You have successfully Created Project......')
        else:
            messages.error(
                request, form.errors)
    if request.path!="/timeline/createproject/":
        return redirect('list-projects')
    return redirect('time_managemnet')
    
#List Project
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
# @allowedGroups('Admin')
def listProjects(request):
    if request.user.role != "Employee":
        dept_groups = request.user.groups.values_list('name',flat = True)
        list_projects = Projects.objects.filter(department__in = dept_groups).annotate(
            act_hrs = Sum('task__timesheet_submission__hours')).order_by('-p_code')
        for obj in list_projects:
            obj.act_hrs = timeline_views.secondToHours(obj.act_hrs)[:-3]
        checklists =  Checklist.objects.all()
        return render(request,'Projects/list-projects.html',
                    {'list':list_projects,"checklist":checklists,"module":"project"})
    return HttpResponse("Sorry!! You are not Authorized")

# EDIT Project pending 
@csrf_exempt
@require_POST
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def editProject(request):
    id = request.POST.get('p_id')
    pk_id = request.POST.get('pk_id')
    projectvalues = Projects.objects.get(pk=pk_id)
    for key, value in request.POST.items():
        if key == 'proj_name':
            projectvalues.name = value
        if key == 'pro_id':
            projectvalues.pid = value
        if key == 'pro_dept':
            projectvalues.department = value
        if key == 'est_hours':
            projectvalues.estimated_hrs = value
        projectvalues.save()
    return redirect('list-projects')

#Delecte Project
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def deleteProject(request,id):
    Projects.objects.get(pk = id).delete()
    return redirect('list-projects')

#Task mange under Each project
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def taskManager(request,id):
    dept_groups = request.user.groups.values_list('name',flat = True)
    Project = Projects.objects.get(pk = id) 
    milestone_templates= Milestone_templates.objects.filter(Q(department=Project.department)).all()
    
    tasks_templates = Task_templates.objects.filter(mid__department=Project.department).all()
    
    milestones = Milestone.objects.filter(pid = id).order_by('name')      

    employees = CustomEmployeeDetails.objects.order_by('first_name').filter(is_active=True,groups__name__in =dept_groups)

    tasks = Task.objects.filter(pid =id).all().order_by('mid__name') 

    project_summary = Task.objects.values('pid').annotate(
                New=Sum(Case(When(status='New', then=1),
                    output_field=IntegerField())),
                Hold=Sum(Case(When(status='Hold', then=1),
                        output_field=IntegerField())),
                Completed=Sum(Case(When(status='Completed', then=1),
                        output_field=IntegerField())),
                Inprogress=Sum(Case(When(status='Inprogress', then=1),
                        output_field=IntegerField())),
                Total=Count('pid')).filter(pid =id)
    return render(request,'Projects/task-manager.html',{"module":"project",'Project':Project,'Milestone':milestones,'employees':employees,
            'tasks':tasks,'tasks_templates':tasks_templates,'milestone_templates':milestone_templates,"project_summary":project_summary})

#Create Milestone under project
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def createMilestone(request,id):
    if request.method == "POST":
        form = MilestoneForm(request.POST)
        if form.is_valid():
            form_data = form.save(commit=False)
            form_data.pid = Projects.objects.get(pk=id)
            form_data.save()
            return redirect('task-manager',id)
        else:
            return JsonResponse({"Error":'Failed to save the milstone data'})

#Edit Milestone under project
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def editMilestone(request,pid):
    id = request.POST.get('id')
    milestone = Milestone.objects.get(pk = id)
    if request.method == "POST":
        form = MilestoneForm(request.POST,instance=milestone)
        if form.is_valid():
            form_data = form.save(commit=False)
            form_data.pid = Projects.objects.get(pk=pid)
            form_data.save()
            return redirect('task-manager',pid)
        else:
            return JsonResponse({"Error":'Failed to save the milstone data'})

#Delete Milestone under project
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def deleteMilestone(request,id,pid):
    Milestone.objects.get(pk = id).delete()
    updateProjectWeightage(pid)
    return redirect('task-manager',pid)


@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def createTask(request,pid):
    if request.method == "POST":
        employee_arg = request.POST.getlist('assigned_to_list')
        for emp in employee_arg:
            Task.objects.create(
                name = request.POST.get('name'),
                pid_id = pid,
                mid_id = request.POST.get('mid_id'),
                start_date = request.POST.get('start_date') ,
                end_date = request.POST.get('end_date') ,
                weightage = request.POST.get('weightage'),
                priority =request.POST.get('priority'),
                assigned_to = emp,
                assigned_by =request.user.first_name,
                status =request.POST.get('status'),
                estimated_hrs =request.POST.get('estimated_hrs'),
                description = request.POST.get('description'),
                quotted_hours=0)
    return redirect('task-manager',pid)

#Edit Task Under Project
@csrf_exempt
@require_POST
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def editTaskAjax(request):
    if request.POST.get('mode') == 'editMilestone':
        m_id =request.POST.get('m_id')
        milstone =Milestone.objects.get(pk =m_id )
        milstone.name = request.POST.get('milestone')
        milstone.save()
    else:
        for key, value in request.POST.items():
            id = request.POST.get('t_id')
            task = Task.objects.get(pk = id)
            if key == 'taskname':
                task.name = value
            if key == 'start_date':
                task.start_date = value
                delta = task.end_date - datetime.datetime.strptime(value, '%Y-%m-%d').date()
                task.estimated_hrs = (delta.days +1) * 9
            if key == 'end_date':
                task.end_date = value
                delta = datetime.datetime.strptime(value, '%Y-%m-%d').date() -task.start_date 
                task.estimated_hrs = (delta.days+1) * 9
            if key == 'weightage':
                task.weightage = value
            if key == 'priority':
                task.priority = value
            if key == 'assigned_to':
                task.assigned_to = value
            if key == 'estimated_hrs':
                task.estimated_hrs = value
            if key == 'priority':
                task.priority = value
            if key == 'description':
                task.description = value
            task.save()
    return JsonResponse({"status":"ok"})

#Delete Task Under Project
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def deleteTask(request,id,mid,pid):
    Task.objects.get(pk = id).delete()
    updateProjectWeightage(pid)
    updateMilestoneWeightage(mid)  
    return redirect('task-manager',pid)

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def gantchartdatefilter(request):
    if request.user.role != "Employee":
        dept_groups = request.user.groups.values_list('name',flat = True)
        dic={}
        projectlist = []
        startdate = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-01')
        enddate = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d')
        project_name_ = Projects.objects.values('name').order_by('name').filter(department__in =dept_groups)
        name = Projects.objects.values('name').order_by('name').filter(department__in =dept_groups)
        Tasks = Task.objects.filter(Q(start_date__range = (startdate,enddate)) | Q(end_date__range = (startdate,enddate)) &
                                     Q(pid__department__in =dept_groups)).values('start_date','end_date','pid__name','name')
        if request.method == "POST":
            startdate = request.POST['startdate']
            enddate = request.POST['enddate']
            proj_name = request.POST['project']
            if proj_name != "All_project":
                Tasks = Task.objects.filter(Q(Q(start_date__range = (startdate,enddate)) | Q(end_date__range = (startdate,enddate))) 
                                            & Q(pid__department__in =dept_groups) & Q(pid__name = proj_name)).values('start_date','end_date','pid__name','name')
                name = Task.objects.filter(Q(Q(start_date__range = (startdate,enddate)) | Q(end_date__range = (startdate,enddate))) 
                                           & Q(pid__department__in =dept_groups)& Q(pid__name = proj_name)).values('name')
                if Tasks:
                    for tsk in Tasks:
                        rgbcolor = "%06x" % random.randint(0, 0xFFFFFF)
                        sdate = datetime.datetime.strftime(tsk['start_date'],'%Y-%m-%d')
                        edate = datetime.datetime.strftime(tsk['end_date'],'%Y-%m-%d')
                        dic['start_date'] = sdate
                        dic['end_date'] = edate
                        dic['name'] = tsk['name']
                        dic['Taskname'] = tsk['name']
                        dic['columnSettings'] = {"fill":'#'+str(rgbcolor)}
                        projectlist.append(dic.copy())
                return render(request, 'Projects/ganttcharttest.html',{'projectlist':projectlist,'name':list(name),'startdate':startdate,'enddate':enddate,"module":"project","project_name_":project_name_})
            else:
                Tasks = Task.objects.filter(Q(start_date__range = (startdate,enddate)) | Q(end_date__range = (startdate,enddate))).values('start_date','end_date','pid__name','name')
        if Tasks:
            for tsk in Tasks:
                rgbcolor = "%06x" % random.randint(0, 0xFFFFFF)
                sdate = datetime.datetime.strftime(tsk['start_date'],'%Y-%m-%d')
                edate = datetime.datetime.strftime(tsk['end_date'],'%Y-%m-%d')
                dic['start_date'] = sdate
                dic['end_date'] = edate
                dic['name'] = tsk['pid__name']
                dic['Taskname'] = tsk['name']
                dic['columnSettings'] = {"fill":'#'+str(rgbcolor)}
                projectlist.append(dic.copy())
        return render(request, 'Projects/ganttcharttest.html',{'projectlist':projectlist,'name':list(name),'startdate':startdate,'enddate':enddate,"module":"project","project_name_":project_name_})
    return HttpResponse("Sorry!! You are not Authorized")
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def get_project_checklist(request,pid):
    project = Projects.objects.get(pid=pid)
    selected_checklist = project.checklists.all()
    data = {"selected_checklist":serializers.serialize('json', selected_checklist)}
    data["checklist"] = serializers.serialize('json',Checklist.objects.all())
    return JsonResponse(data=data,safe=False)

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def add_checklist_to_project(request):
    if request.method == "POST":
        value = dict(request.POST)
        del value["csrfmiddlewaretoken"]
        p_name= value.pop('name')
        checklists_id = value.keys()
        checklist = Checklist.objects.filter(id__in=checklists_id)
        project = Projects.objects.get(name = p_name[0])
        project.checklists.clear()
        project.checklists.add(*checklist)
        project.save()
        return redirect('list-projects')

# create Task with null value from timesheet module
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def creatreTaskAjax(request):
    Task.objects.create(
    name ="Task",
    pid = Projects.objects.get(pk=request.POST.get('pid')),
    mid = Milestone.objects.get(pk=request.POST.get('mid')),
    start_date = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d') ,
    end_date = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d') ,
    weightage = 10,
    priority ="Medium",
    assigned_to ="Name",
    assigned_by =request.user.name,
    status ="New",
    estimated_hrs =10,
    description = "New task")
    return redirect('task-manager',request.POST.get('pid'))
           
def updateProjectWeightage(pid):
    project = Projects.objects.get(id = pid)
    total_weightage = Task.objects.filter(pid_id = pid).aggregate(Sum('weightage'))
    completed_weightage = Task.objects.filter(pid_id = pid,status = 'Completed').aggregate(Sum('weightage'))
    weightage = 0
    if completed_weightage['weightage__sum'] != None:
        try:
            weightage = completed_weightage['weightage__sum']/total_weightage['weightage__sum']
        except:
            weightage = 0
    # print(total_weightage,completed_weightage,round(weightage,2)*100)
    project.weightage = round(weightage,2)*100
    project.save()

def updateMilestoneWeightage(mid):
    milestone = Milestone.objects.get(pk=mid)
    total_weightage = Task.objects.filter(mid_id = mid).aggregate(Sum('weightage'))
    completed_weightage = Task.objects.filter(mid_id = mid,status = 'Completed').aggregate(Sum('weightage'))
    weightage = 0
    if completed_weightage['weightage__sum'] != None:
        try:
            weightage = completed_weightage['weightage__sum']/total_weightage['weightage__sum']
        except:
            weightage = 0
    milestone.weightage = round(weightage,2)*100
    milestone.save()   

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

# Resource Planning
def resourceplanning(request):
    if request.user.role != "Employee":
        return render(request,'Projects/resource_palanning.html',{"module":"project"})
    return HttpResponse("Sorry!! You are not Authorized")
@csrf_protect
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def getPlandetails(request):
    dept_groups = request.user.groups.values_list('name',flat = True)
    department =dept_groups[0]
    columns =["Name"]
    date = datetime.datetime.now().replace(day=1)
    headerDate =date
    celldate = date
    tbl_data ={}
    data =[]
    if request.method == 'POST':
        department = request.POST.get('Department')
        date = datetime.datetime.strptime(request.POST.get('month'),'%Y-%m') 
        headerDate = date
        celldate = date
    for i in range(30): 
        day = datetime.datetime.strftime(headerDate,'%d')
        headerDate += datetime.timedelta(days=1) 
        columns.append(day)

    tbl_data["columns"] = columns
    employee_List =CustomEmployeeDetails.objects.filter(Q(is_active =True) & 
                                                        Q(groups__name = department)).values('first_name').order_by('first_name')
    for obj in employee_List:
        row_data = [obj['first_name']]
        temp = celldate 
        for i in range(30):
            day = datetime.datetime.strftime(temp,'%Y-%m-%d')
            tasks = Task.objects.filter(Q(assigned_to = obj['first_name']) & Q(end_date__gte = day,start_date__lte =day))
            if datetime.datetime.strftime(temp,'%A') !='Sunday':
                if not tasks:
                    row_data.append(None)
                else:
                    t =""
                    if len(tasks) > 1:
                        for task in tasks:
                            t = t + task.pid.name+' : '+task.name+'\n'
                        row_data.append(t)
                    else:
                        row_data.append(tasks[0].pid.name +" : "+ tasks[0].name)
            else:
                row_data.append( datetime.datetime.strftime(temp,'%A'))

            temp += datetime.timedelta(days=1)
        data.append(row_data)
    tbl_data["columns"] = columns
    tbl_data["data"] = data
    return JsonResponse({'tbl_data':tbl_data,"Department":list(dept_groups),"month": datetime.datetime.strftime(date,'%Y-%m')})

# Templates 
# list templates
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def list_templates(request):
    return render(request,'Projects/list_templates.html',{"module":"settings"})

@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def listtemplate_task(request):
    department_list = Group.objects.values_list('name',flat = True).exclude(name = 'Admin')
    dept = department_list[0]
    if request.method == "POST":
        dept = request.POST.get('dept')
        cdict = {key:value for key,value in request.POST.items()}
        if cdict['mode'] == "edit_table":
            if 'milestonename' in cdict:
                milestone = Milestone_templates.objects.get(pk = cdict['milstnid'])
                milestone.milestone = cdict['milestonename']
                milestone.save()
            else:
                task = Task_templates.objects.get(pk = cdict['tskid'])
                task.task = cdict['taskname']                                         
                task.save()
        if cdict['mode'] == "deletedata":
            if 'tskid' in cdict:
                Task_templates.objects.get(pk = cdict['tskid']).delete()
            else:
                Milestone_templates.objects.get(pk = cdict['milstnid']).delete()
    tasklist= Milestone_templates.objects.values('id','milestone','department','task_templates__task','task_templates__id').filter(department = dept)
    return JsonResponse({'department_list':list(department_list),'tasklist':list(tasklist)})

# Add milestone templates
@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='home')
def add_milestone(request):
    if request.method == "POST":
        form = templates_milestone_form(request.POST)
        if form.is_valid():
            form.save()
            department = request.POST.get('department')
            tasklist= Milestone_templates.objects.values('id','milestone','department','task_templates__task','task_templates__id').filter(department = department)
            return JsonResponse({"tasklist":list(tasklist)})
        else:
            return JsonResponse({"Error":'Failed to save the task data'})
    # else:
    #     form = templates_milestone_form()
    # return redirect('list-templates')

# Add Taks templates 
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def add_task(request):
    mid = request.POST.get('mid')
    if request.method == "POST":
        form = templates_task_form(request.POST)
        if form.is_valid():
            form_data = form.save(commit=False)
            milestone = Milestone_templates.objects.get(pk=mid)
            form_data.mid = milestone
            form_data.save()
            tasklist= Milestone_templates.objects.values('id','milestone','department','task_templates__task','task_templates__id').filter(department = milestone.department)
            return JsonResponse({"tasklist":list(tasklist)})
        else:
            return JsonResponse({"Error":'Failed to save the task data'})

# Delete Templates
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def delete_milestone_template(request,id):
    Milestone_templates.objects.get(id = id).delete() 
    return redirect('list-templates')

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def delete_task_templates(request,id,mid):
    Task_templates.objects.get(id = id).delete()
    return redirect('list-templates')

#Edit_Load_templates
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def Edit_Load_templates(request,id):
   
    start_dtate = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d') 
    end_date = timezone.now() + datetime.timedelta(days=5)
    milestone_arg = request.POST.getlist('milestone_template_list')
    milestone_temp_list= Milestone_templates.objects.filter(id__in =milestone_arg)
    if request.method == "POST":
        for m_obj in  milestone_temp_list:
            Milestone.objects.create(
                name= m_obj.milestone,
                weightage=1,
                pid_id=id
            )
            milestone_id = Milestone.objects.values('id').filter(Q(name = m_obj.milestone)&Q(pid_id = id)).order_by('-updated_date')[:1]
            task_template_name = Task_templates.objects.filter(mid = m_obj.id)
            for t_obj in task_template_name:
                Task.objects.create(
                    name = t_obj.task,
                    pid_id = id,
                    mid_id = milestone_id,
                    start_date = start_dtate,
                    end_date = end_date,
                    weightage = 10,
                    priority ="Medium",
                    assigned_to =request.user.first_name,
                    assigned_by =request.user.first_name,
                    status ="New",
                    estimated_hrs =10,
                    description = "New task",
                    quotted_hours=0)
    return redirect('task-manager',id)

#create task using milestone template

@csrf_exempt
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def create_task_using_mtemplate(request):
    if request.method == "POST":
        projectname = request.POST.get('projectName')
        
        taskname = request.POST.get('taskName')

        departmentname = request.POST.get('deptName')
        
        fromdate_=datetime.datetime.strptime(request.POST.get('fromdate_'),'%d-%b-%Y')
        
        todate_ = datetime.datetime.strptime(request.POST.get('todate_'),'%d-%b-%Y')
        
        milestone = Task_templates.objects.values("mid__milestone").filter(Q(task = taskname) & 
                                                                           Q(mid__department=departmentname))

        project_id = Projects.objects.values('id').filter(Q(name = projectname) & 
                                                          Q(department = departmentname))

        existingTask = Task.objects.values('id','assigned_to','mid_id','pid_id').filter(Q(name = taskname) & 
                                                        Q(pid__name = projectname) & 
                                                        Q(mid__name = milestone[0]["mid__milestone"]) & 
                                                        Q(pid__department=departmentname))
        
        if existingTask:
            if not existingTask[0]['assigned_to']:
                task_object = Task.objects.get(pk=existingTask[0]['id'])
                task_object.assigned_by = request.user.first_name
                task_object.assigned_to = request.user.first_name
                task_object.end_date = todate_ 
                task_object.save()
            else:
                result = next((sub for sub in existingTask if sub['assigned_to'] == request.user.first_name), None)
                if result:
                    task_object = Task.objects.get(pk=result['id'])
                    if task_object.start_date > fromdate_.date():
                        task_object.start_date = fromdate_
                    else:
                        task_object.end_date = todate_ 
                    task_object.save()
                else:
                    Task.objects.create(
                        name = taskname,
                        pid_id = existingTask[0]["pid_id"],
                        mid_id = existingTask[0]["mid_id"],
                        start_date = fromdate_,
                        end_date = todate_,
                        priority ="Medium",
                        assigned_to =request.user.first_name,
                        assigned_by =request.user.first_name,
                        status ="New",
                        description = "New task",
                        quotted_hours=0)
        else:
            Milestone.objects.create(
                name= milestone[0]["mid__milestone"],
                weightage=1,
                pid_id= project_id[0]["id"]
            )
            milestone_id = Milestone.objects.values('id').filter(Q(name = milestone[0]["mid__milestone"])&Q(pid_id = project_id[0]["id"])).order_by('-updated_date')[:1]
            Task.objects.create(
                name = taskname,
                pid_id = project_id[0]["id"],
                mid_id = milestone_id[0]["id"],
                start_date = fromdate_,
                end_date = todate_,
                priority ="Medium",
                assigned_to =request.user.first_name,
                assigned_by =request.user.first_name,
                status ="New",
                description = "New task",
                quotted_hours=0)
    return redirect('get_time_sheet_templete')

@csrf_exempt
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def task_summary(request):
    if request.user.role != "Employee":
        return render(request,'Projects/task_summary.html',{"module":"project"})
    return HttpResponse("Sorry!! You are not Authorized")
@csrf_exempt
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def loadtasksummary_table(request):
    active = True
    dept_groups = request.user.groups.values_list('name',flat = True)
    if request.method == 'POST':
        active = False if request.POST.get('checked')  == "false" else True
    tasks = Task.objects.values('pid__name').annotate(
                    New=Sum(Case(When(status='New', then=1),
                        output_field=IntegerField())),
                    Hold=Sum(Case(When(status='Hold', then=1),
                            output_field=IntegerField())),
                    Completed=Sum(Case(When(status='Completed', then=1),
                            output_field=IntegerField())),
                    Inprogress=Sum(Case(When(status='Inprogress', then=1),
                            output_field=IntegerField())),
                    Total=Count('pid')).order_by('pid').filter(Q(pid__is_active=active)&Q(pid__department__in =dept_groups))
    return JsonResponse({'tasks':list(tasks),"active":active})
    
#Check list
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def create_checklist(request):
    if request.method == "POST":
        checklist_name = request.POST.get('clname').lower()
        remarks = request.POST.get('clremarks')
        checklist = Checklist(name=checklist_name,remarks=remarks)
        checklist.save()
        messages.success(
                request, f'You have successfully created checklist: {checklist_name}...')
    return redirect('list-checklist')

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def edit_checklist_details(request,checklist_id):
    if request.method == 'POST':
        checklist_name = request.POST.get('clname').lower()
        remarks = request.POST.get('clremarks')
        checklist = Checklist.objects.get(id=checklist_id)
        checklist.name = checklist_name
        checklist.remarks = remarks
        checklist.save()
    return redirect('list-checklist')


@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def validate_checklist_name(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        checklist = Checklist.objects.filter(name=data['checklist_name'].lower()).exists()
        if checklist:
            return  JsonResponse({"status":"exists"},safe=False)
    return  JsonResponse({"status":"not_exists"},safe=False)
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def list_checklist(request):
    checklist = Checklist.objects.all()
    return render(request, 'checklist/list_checklist.html', {'checklist':checklist,"module":"settings"})

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def edit_checklist(request,checklist_id):
    checklist = Checklist.objects.get(id=checklist_id)
    if request.method=="POST":
        if "new_section" in request.POST:
            section_name = request.POST.get('section_name').lower()
            section = Section(name=section_name)
            section.save()
            checklist = Checklist.objects.get(id=checklist_id)
            checklist.section.add(section)
            checklist.save()
        if "add_section" in request.POST:
            query = dict(request.POST)
            del query["csrfmiddlewaretoken"]
            del query["add_section"]
            query = [int(q) for q in query ]
            checked_sections = Section.objects.filter(id__in=query)
            checklist.section.clear()
            checklist.section.set(checked_sections)
    
    sel_sections = checklist.section.all()
    if len(sel_sections) > 0:
        return redirect('view-section', c_id=checklist_id, s_id=sel_sections[0].id)
    sel_questions = Question.objects.filter(section__in=sel_sections)
    sections = Section.objects.exclude(id__in=sel_sections)
    questions = Question.objects.exclude(id__in=sel_questions) 
   

    return render(request,"checklist/edit_checklist.html",{"questions":questions,"sections":sections,
                                                          "sel_questions":sel_questions,"sel_sections":sel_sections,
                                                          "current_checklist":checklist,})

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def view_sections(request,c_id,s_id):
    current_checklist = Checklist.objects.get(id=c_id)
    current_section = current_checklist.section.get(id=s_id)
    if request.method=="POST":
        if "new_section" in request.POST :
            section_name = request.POST.get('section_name').lower()
            checklist = Checklist.objects.get(id=c_id)
            section = Section(name=section_name)
            section.save()
            checklist.section.add(section)
            checklist.save()
        if "edit_section" in request.POST:
            print("in edit section")
            current_section.name = request.POST.get('section_name').lower()
            current_section.save()
        if "add_section" in request.POST:
            query = dict(request.POST)
            del query["csrfmiddlewaretoken"]
            del query["add_section"]
            query = [int(q) for q in query ]
            checked_sections = Section.objects.filter(id__in=query)
            current_checklist.section.clear()
            current_checklist.section.set(checked_sections)
        if "add_question" in request.POST:
            query = dict(request.POST)
            del query["csrfmiddlewaretoken"]
            del query["add_question"]
            query = [int(q) for q in query ]
            checked_questions = Question.objects.filter(id__in=query)
            current_section.question.clear()
            current_section.question.set(checked_questions)
        if "new_question" in request.POST:
            query = dict(request.POST)
            del query["csrfmiddlewaretoken"]
            del query["new_question"]
            transaction.set_autocommit(False)
            try:
                opt = []
                for qoption in query["options"]:
                    option = QuestionOption.objects.filter(option=qoption)
                    if option.exists():
                        opt.append(option.first().id)
                    else:
                        option = QuestionOption(option=qoption)
                        option.save()
                        opt.append(option.id)
                questions = Question(question=query["question"][0].lower(),type=query["type"][0],attachment=request.FILES.get("file_name"))
                questions.save()
                questions.options.set(opt)
                checklist_obj = Checklist.objects.get(id=c_id)
                section_obj = checklist_obj.section.get(id=s_id)
                section_obj.question.add(questions)
            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()
            finally:
                transaction.set_autocommit(True)
            #new_question = Question(question=query['question'])
        
            # checked_questions = Question.objects.filter(id__in=query)
            # section.question.set(checked_questions)
    
    sel_sections = current_checklist.section.all()
    sections = Section.objects.exclude(id__in=sel_sections)
    sel_questions = current_section.question.all()
    questions = Question.objects.exclude(id__in=sel_questions)
    return render(request,"checklist/edit_sections.html",{"sections":sections,
                                                          "sel_sections":sel_sections,
                                                          "questions":questions,
                                                          "sel_questions":sel_questions,
                                                          "current_section":current_section,
                                                          "current_checklist":current_checklist})

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def validate_section_name(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        checklist = Checklist.objects.get(id=data['checklist_id'])
        if data['section_name'].lower() in [section.name.lower() for section in checklist.section.all()]:
            print("section_name exists")
            return  JsonResponse({"status":"exists"},safe=False)
    return  JsonResponse({"status":"not_exists"},safe=False)


@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def validate_question_name(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        section = Section.objects.get(id=data["section_id"])
        if data['question'].lower() in [question.question.lower() for question in section.question.all()]:
            print("question exists")
            return  JsonResponse({"status":"exists"},safe=False)
    return  JsonResponse({"status":"not_exists"},safe=False)

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def edit_question(request,c_id,s_id,q_id):
    if "edit_question" in request.POST:
            query = dict(request.POST)
            del query["csrfmiddlewaretoken"]
            del query["edit_question"]
            transaction.set_autocommit(False)
            try:
                opt = []
                if query["type"][0]=='radio':
                    for qoption in query["options"]:
                        option = QuestionOption.objects.filter(option=qoption)
                        if option:
                            opt.append(option.first().id)
                        else:
                            option = QuestionOption(option=qoption)
                            option.save()
                            opt.append(option.id)  

                question = Question.objects.get(id=q_id)
                question.question = query["question"][0].lower()
                question.type=query["type"][0]
                if request.FILES.get("file_name") is not None:
                    question.attachment = request.FILES.get("file_name")
                question.options.set(opt)
                question.save()
            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()
            finally:
                transaction.set_autocommit(True)
    return redirect('view-section',c_id=c_id,s_id=s_id)


@login_required(login_url='home')
@unathenticated
@allowedGroups(allowedgroup=['Admin'])
def delete_checklist(request,checklist_id):
    checklist = Checklist.objects.get(id=checklist_id)
    projects_related = [ project.id for project in checklist.projects_set.all() ]
    if len(projects_related) == 0:
        checklist_name = checklist.name.lower()
        checklist.delete()
        messages.success(request, f"{checklist_name} deleted succesfully")
    else:
        messages.error(request,f"{checklist.name} in use by other project(s), cannot be deleted")
    return redirect('list-checklist')


@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def view_checklist(request,p_id,c_id):
    project = Projects.objects.get(id=p_id)
    checklist = project.checklists.get(id=c_id)
    sections = checklist.section.all()
    if len(sections)>0:
        c_id = checklist.id
        s_id = sections[0].id
        return redirect('view-section',c_id=c_id,s_id=s_id)
    return render(request,"checklist/view_checklist.html",{"current_checklist":checklist,                                                       
                                                           "project":project})

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def get_questions(request,p_id,c_id,s_id):
    project = Projects.objects.get(id=p_id)
    checklist = project.checklists.get(id=c_id)
    section = checklist.section.get(id=s_id)
    questions = section.question.all()
    return render(request,"checklist/view_sections.html",{"questions":questions,"checklist":checklist})

def get_question(request,q_id):    
    question = Question.objects.get(id=q_id)
    data = {}
    data['question']=question.question
    data['type']=question.type
    data['attachment']={}
    data['attachment']['name']=question.attachment.name
    data['attachment']['link']=f"/projects/checklist/attachment/{q_id}"
    options = [ option.option for option in question.options.all() ]
    data['option']=options  
    return JsonResponse(data,safe=False)


@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def get_project_checklists(request,p_id, audit=None):
    project = Projects.objects.get(id=p_id)
    checklist_id = project.checklists.all()[0].id
    if audit == None:
        return redirect("get-c-sections", p_id=p_id, c_id=checklist_id)
    else:
        return redirect("get-c-sections", p_id=p_id, c_id=checklist_id, audit=audit)

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def get_checklist_sections(request,p_id,c_id,audit=None):
    project = Projects.objects.get(id=p_id)
    current_checklist = project.checklists.get(id=c_id)
    current_section = current_checklist.section.all()[0].id
    if audit == None:
        return redirect("get-s-questions", p_id=p_id, c_id=c_id, s_id=current_section)
    else:
        return redirect("get-s-questions", p_id=p_id, c_id=c_id, s_id=current_section,audit=audit)

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def get_section_questions(request,p_id,c_id,s_id,audit=None):
    if audit == 'audit':
        audit = True
    project = Projects.objects.get(id=p_id)
    checklists = project.checklists.all()
    current_checklist = project.checklists.get(id=c_id)
    sections = current_checklist.section.all()
    if s_id is None:
        current_section = sections[0]
    else:
        current_section = current_checklist.section.get(id=s_id)
    
    questions = current_section.question.all()
    answers = Answer.objects.filter(Q(checklist=current_checklist.id) & Q(section=current_section.id))
    answered_questions = [answer.question for answer in answers]
    print(request.POST)
    if audit == None:
        if request.method == 'POST':
            for question in current_section.question.all():
                answer = Answer.objects.filter(Q(checklist=current_checklist.id) & Q(section=current_section.id) & Q(question=question.id) )
                
                if answer.exists():
                    answer.update(text=request.POST.get(f"question{question.id}"))
                    answer.update(remarks=request.POST.get(f"remarks{question.id}"))                     
                        
                else:
                    answer = Answer(
                        question=question,
                        checklist=current_checklist,
                        section=current_section,
                        project=project,
                        text=request.POST.get(f"question{question.id}"),
                        remarks=request.POST.get(f"remarks{question.id}")
                        )
                    answer.save()
                    
        answers = Answer.objects.filter(Q(checklist=current_checklist.id) & Q(section=current_section.id))
        answered_questions = [answer.question for answer in answers]
        return render(request,'checklist/answer_checklist.html',{"project":project,
                                                                "current_checklist":current_checklist,
                                                                "current_section":current_section,
                                                                "checklists":checklists,
                                                                "sections":sections,
                                                                "questions":questions,
                                                                "answers":answers,
                                                                "answered_questions":answered_questions,
                                                                })
    else:
        return render(request,'checklist/answer_checklist.html',{"project":project,
                                                                "current_checklist":current_checklist,
                                                                "current_section":current_section,
                                                                "checklists":checklists,
                                                                "sections":sections,
                                                                "questions":questions,
                                                                "answers":answers,
                                                                "answered_questions":answered_questions,
                                                                "audit":audit})
    
@login_required(login_url='home')
@unathenticated
@allowedGroups(allowedgroup=['Admin'])
def delete_question(request,c_id,s_id,q_id):
    question = Question.objects.get(id=q_id)
    question.delete()
    return redirect('view-section',c_id=c_id,s_id=s_id)

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def delete_section(request,c_id,s_id):
    section = Section.objects.get(id=s_id)
    section.delete()
    return redirect('edit-checklist',checklist_id=c_id)

def download_question_attachment(request,question_id):
    
    question = get_object_or_404(Question, pk=question_id)
    response = HttpResponse(question.attachment, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{question.attachment.name}"'
    return response


def download_project_pdf(request,project_id):                                 
           
    project = Projects.objects.get(id=project_id)
    answers = []
    for checklist in project.checklists.all():
        for section in checklist.section.all():
            for i,question in enumerate(section.question.all()):
                answer = Answer.objects.filter(Q(checklist=checklist.id) & Q(section=section.id) & Q(question=question.id)).first()
                if answer:
                    answers.append(answer)
                else:
                    if question.type == 'text':
                        current_anwser = Answer(
                        checklist=checklist,
                        section=section,
                        question=question,
                        text="Not Answered",
                        remarks="NA"
                        )
                    else:
                        current_anwser = Answer(
                        checklist=checklist,
                        section=section,
                        question=question,
                        text="Not Answered",
                        remarks="Not Answered"
                        )
                    answers.append(current_anwser)

    return render(request,'checklist/checklist_report.html',{'project':project,
                                                             "answers":answers}) 