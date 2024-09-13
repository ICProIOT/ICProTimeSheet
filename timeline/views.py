import json
from re import sub
from projects.models import Projects, Task,Task_templates,Milestone
from typing import cast
from .models import timesheet_submission
from Employee.models import CustomEmployeeDetails
from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.models import Group, User,auth
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.db.models.functions import Extract,ExtractDay,Cast
from django.db.models import F, Func, Value, CharField
from django.db.models import CharField, Value as V
from django.db.models.functions import Concat
from django_mysql.models import GroupConcat
from Employee.decorators import unathenticated,allowedGroups
from django.contrib.auth.decorators import login_required
from django.db.models import Q,Sum,OuterRef, Subquery,Prefetch
from itertools import chain
from calendar import calendar
from file_management.models import feeds
from datetime import date , timedelta,datetime
from django.views.decorators.csrf import csrf_exempt,csrf_protect
from django.views.decorators.http import require_POST
import pandas as pd
import numpy as np
from projects.forms import ProjectForm
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.views.decorators.cache import cache_control


# Create your views here.
# Submission
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def submission(request):
    return render(request,'submission.html',{'module':"timesheet"})

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@csrf_exempt
def submission_templete(request):
    dept_groups = request.user.groups.values_list('name',flat = True)

    # columns =["Task","TID"]
    year = datetime.today().year
    week = datetime.today().strftime("%V")

    d = str(year)+'-'+ week
    # week start from Saturday
    if  datetime.today().weekday()>= 5:
        week_start_date =datetime.strptime(d + '-1', "%Y-%W-%w") + timedelta(days=5) 
    else: 
        week_start_date =datetime.strptime(d + '-1', "%Y-%W-%w") - timedelta(days=2) 
        
    start_date = week_start_date

    To_date = week_start_date + timedelta(days=6)

    assigned_projects = request.user.projects_set.values().order_by('name')

    projects_list  = Projects.objects.values('name','department','id').filter(department__in =dept_groups).order_by('name')
    
    tasknames = Task_templates.objects.values('task','mid__department')

    milestone = Milestone.objects.values('name')

    tbl_data ={}
    
    if request.method == 'POST':
        presentweek_start_date = datetime.strptime(request.POST.get('fromdate_'),'%d-%b-%Y')
        mode = request.POST.get('mode')
        if mode=='postdate':
            week_start_date = presentweek_start_date + timedelta(days=7)
            start_date = week_start_date
            To_date = presentweek_start_date + timedelta(days=13)
        elif mode=='predate': 
            week_start_date = presentweek_start_date - timedelta(days=7)
            start_date = week_start_date
            To_date =presentweek_start_date - timedelta(days=1)
        elif mode=='delete':
            weekenddate = presentweek_start_date +timedelta(days=7)
            task = Task.objects.get(id = request.POST.get('task_id'))
            if presentweek_start_date.date() <= task.start_date <= weekenddate.date():
                task.delete()
            else:
                submitedData = timesheet_submission.objects.values('id').filter(Q(uid__first_name  = request.user.first_name) 
                                                        & Q(date__range=[presentweek_start_date, presentweek_start_date+timedelta(days=7)]) 
                                                        &Q(task_id = request.POST.get('task_id'))).order_by('date')
                if submitedData:
                    for item in submitedData:
                        timesheet_submission.objects.get(pk =item['id']).delete()
                task.end_date =  datetime.strftime(presentweek_start_date-timedelta(days=1),'%Y-%m-%d')
                task.save()
        elif mode=='extend':
            extend_To_date = presentweek_start_date + timedelta(days=7)
            tasks = Task.objects.values('id').filter(~Q(status = "Completed" ) & Q(assigned_to  = request.user.first_name) 
                                                      & Q(end_date__range=[presentweek_start_date, extend_To_date])).order_by('name')
            for item in tasks:
                task = Task.objects.get(pk=item['id'])
                task.end_date = datetime.strftime(task.end_date+timedelta(days=7),'%Y-%m-%d')
                task.save()
        elif mode =='comment':
            task_id = request.POST.get('task_id')
            index_date = request.POST.get('index_num')
            comment = request.POST.get('comment')
            update_comment_id = timesheet_submission.objects.values('id').filter(Q(date=index_date) & Q(task_id=task_id))
            if update_comment_id:
                update_comment = timesheet_submission.objects.get(pk=update_comment_id[0]['id'])
                update_comment.comment = comment
                update_comment.save()

        elif mode=='visible':
            request.user.projects_set.clear()
            for i in json.loads(request.POST.get('proj_id')):#convert json string to json object 
                my_projects = Projects.objects.get(pk=i)
                my_projects.uid.add(request.user)

        elif mode=='edithours':
            week_start_date = presentweek_start_date
            start_date = week_start_date
            To_date = presentweek_start_date + timedelta(days=6)
            result = edit_hours(request)
            if result['status'] != "valid":
                return JsonResponse (result)
        else:
            from_date = request.POST.get('fromdate_')
            dateRange = [d.strftime('%Y-%m-%d') for d in pd.date_range(from_date, periods=7) ]
            for day in dateRange:
                imeshhetsubmissio_id=timesheet_submission.objects.values('id').filter(Q(uid = request.user.id) & Q(date= day))
                if imeshhetsubmissio_id:
                    for day_i in imeshhetsubmissio_id:
                        update_submission = timesheet_submission.objects.get(pk=day_i['id'])
                        update_submission.submission_status= 'Submitted' if request.user.username != request.user.reporting_to else 'Accepted'
                        update_submission.save()
    
    ############# *********************New method******************#######################
    newData =[] 
    newFooter=[]   
    weekDays=[]               
    assigendTask = Task.objects.filter(~Q(status = "Completed" ) & Q(assigned_to  = request.user.first_name) & 
                                        Q(end_date__gte=week_start_date) & Q(start_date__lte=To_date)).values(
                                                'pid__name','name','id',
                                                'timesheet_submission__date',
                                                'timesheet_submission__hours','mid__name',
                                                ).order_by('pid__name')  
    tableHeader =["Task","TID"]+ [datetime.strftime(d,'%a-%d') for d in pd.date_range(start_date, periods=7)]+['Total']
    if assigendTask: 
        df = pd.DataFrame(assigendTask)  
        df = df.drop_duplicates(subset=['pid__name', 'mid__name','name', 'timesheet_submission__date'], keep='last')
       
        dfPivot = df.pivot(index=['pid__name','mid__name','name','id',],columns='timesheet_submission__date',values='timesheet_submission__hours')
        df2 = dfPivot.reset_index().rename_axis(None, axis=1)
        weekDays =[d.date() for d in pd.date_range(start_date, periods=7)]
        header = ['pid__name','mid__name','name','id']
        df2 =df2.fillna(0)
        for day in weekDays:
            if day not in df2:
                df2[day] = 0
        df2 = df2.reindex(header + weekDays, axis=1)
        df2['weektotal']=df2.iloc[:,4:].sum(axis=1)                                    
        row_sum = df2.iloc[:,4:].sum()
        
        df2.loc[len(df2)] = row_sum
        # df2 = df2.fillna('Total') 
        
        newData = [list(df2.iloc[i]) for i in range(len(df2)-1)]
        newFooter= list(df2.iloc[len(df2)-1])[4:]
  
    submited_status_ = timesheet_submission.objects.values('submission_status').filter(Q(uid = request.user.id) & Q(date__range=[start_date,To_date])).distinct()
    
    submited_status = submited_status_[0]['submission_status'] if submited_status_ else ''
   
    tbl_data["columns"] = tableHeader
    tbl_data["data"] = newData
    return JsonResponse({'tbl_data':tbl_data, 'projects_list':list(projects_list),'assigned_projects':list(assigned_projects),
                         "submited_status":submited_status,'footertotals':newFooter,"weeknumber":week_start_date.strftime("%V"),
                        "from_date":datetime.strftime(start_date,'%d-%b-%Y'),"to_date":datetime.strftime(To_date,'%d-%b-%Y'),
                        "tasks":list(tasknames),"Milestone_names":list(milestone),"cell_date":list(weekDays)})

#fill hours
def edit_hours(request):
    date = request.POST.get('date')
    task_id = request.POST.get('task_id')
    hours = request.POST.get('hours')
    submission_data=timesheet_submission.objects.values('id').filter(Q(uid = request.user.id) & Q(task_id_id  = task_id) & Q(date = date))

    hrsPerday = timesheet_submission.objects.filter(Q(uid = request.user.id) & Q(date = date)).exclude(task_id_id  = task_id).aggregate(sum_colum=Sum('hours'))
    if hours.__contains__('.'):
        duration = timedelta(hours = int(hours.split('.')[0]) if hours.split('.')[0] != '' else 0 
                            ,minutes = int(hours.split('.')[1]) if hours.split('.')[1] != '' else 0 ).total_seconds()
    else:
        duration = timedelta(hours = int(hours.split('.')[0]) if hours.split('.')[0] != '' else 0 ).total_seconds()

    duration_  = duration + hrsPerday['sum_colum'] if hrsPerday['sum_colum'] else duration
    if duration_ <=50400:
        if not submission_data:
            submission_model = timesheet_submission(
                            uid_id = request.user.id,
                            date=date,
                            hours=duration,
                            comment='', 
                            submission_status=None,
                            task_id_id=task_id)
        else:
            submission_model=timesheet_submission.objects.get(pk=submission_data[0]['id'])
            if duration !=0.0:
                submission_model.hours=duration
            else:
                submission_model.delete()
        if duration!=0.0:
            submission_model.save()
        return {"status":"valid"}
    else:
        return {"status":"invalid"}

# get timesheet object
@csrf_exempt
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def getTaskSubmission(request):
    if request.method=="POST":
        if 'submissionID' in request.POST:
            submitedObject = timesheet_submission.objects.get(pk=request.POST.get('submissionID'))
            submitedObject.comment=request.POST.get('comment')
            submitedObject.save()
            data =timesheet_submission.objects.filter(id = request.POST.get('submissionID')).values('comment','id')
        else:
            data =timesheet_submission.objects.filter(date = request.POST.get('date'),
                                            task_id = request.POST.get('task_id'),
                                            uid= request.user).values('comment','id')
            
    return JsonResponse({'data':list(data)})


@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def timemanagement(request):
    if request.user.role != "Employee":
        return render(request,'timemanagement.html',{"module":"timesheet"})  
    return HttpResponse("Sorry!! You are not Authorized")

@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def proj_tabledata(request):
    dept_groups = request.user.groups.values_list('name',flat = True)
    department =dept_groups[0]
    if request.method =='POST':
        department=request.POST.get('department')
        if 'mode' not in request.POST:
            form = ProjectForm(request.POST)
            if form.is_valid():
                form.save()
            else:
                return JsonResponse({"formError":form.errors.as_json()})
        else:
            mode = request.POST.get('mode')
            if mode != 'dept_change':
                projectObject =Projects.objects.get(pk = request.POST.get('pid'))
                if mode =='update':
                    projectObject.name = request.POST.get('name')
                    projectObject.department = request.POST.get('department')
                    projectObject.p_code = request.POST.get('project_code')
                    projectObject.save()
                if mode =='delete':
                    projectObject.delete()
    proj_list=Projects.objects.values('name','department','id','p_code').annotate(budget_hours =Sum('task__quotted_hours')).filter(department =department)
    return JsonResponse({'proj_list':list(proj_list),'dept_groups':list(dept_groups)})

@csrf_exempt
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def template_project(request,id):
    project_name = Projects.objects.values('name').get(pk=id)
    return render(request,'template_project.html',{'id':id,'project_name':project_name['name'],"module":"timesheet"})

# getting templets task and fill task into project minlestone ang task 
@csrf_exempt
@require_POST
def tabledata_project(request):
   
    id = request.POST.get('id')
    project_list = Projects.objects.get(pk=id)
    tasklist = Task_templates.objects.values('mid__milestone','task','id').filter(mid__department = project_list.department).order_by('mid__milestone')
    for i in tasklist:
        i['quotted_hours']=0
    budget_hrs = Task.objects.values('quotted_hours','name','mid__name').filter(pid=id).exclude(quotted_hours = 0).order_by('mid__name')
    if budget_hrs:
        for i in tasklist:
            for j in budget_hrs:
                if i['task']==j['name'] and j['mid__name'] == i['mid__milestone']:
                    i['quotted_hours']=j['quotted_hours']
                    break 
    budget_totalhrs = Task.objects.filter(pid=id).aggregate(budgettotal=Sum('quotted_hours'))
    return JsonResponse({'tasklist':list(tasklist),"budget_totalhrs":budget_totalhrs})

@csrf_exempt
@require_POST
def edit_tabledata(request):
    if request.method =='POST':
        taskTemplete =Task_templates.objects.get(pk=request.POST.get('id'))
        quotted_hours = request.POST.get('quotted_hours')
        milestone_name=taskTemplete.mid.milestone
        task_name =taskTemplete.task
        pid = request.POST.get('p_id')
        milestone_data = Milestone.objects.values('id').filter(Q( name = milestone_name ) & Q(pid  =  pid))
        if milestone_data:
            task_data = Task.objects.values('id').filter(Q( pid = pid ) & Q(mid  = milestone_data[0]["id"]) & Q(name  =  task_name))
            if task_data:
                task_values = Task.objects.get(pk = task_data[0]['id'])
                task_values.quotted_hours = quotted_hours
                task_values.save()
            else:
                task = Task(
                    name = task_name,
                    start_date = datetime.strftime(datetime.now(),'%Y-%m-%d'),
                    end_date = datetime.strftime(datetime.now(),'%Y-%m-%d'),
                    weightage = 1,
                    priority = 'High',
                    assigned_to = '',
                    status = 'New',
                    description = task_name,
                    assigned_by = '',
                    mid_id = milestone_data[0]["id"],
                    pid_id = pid,
                    quotted_hours = quotted_hours
                )
                task.save()
        else:
            milestone = Milestone(
                name = milestone_name,
                weightage = 1,
                pid_id = pid
            )
            milestone.save()
            mid = Milestone.objects.latest('id')
            task = Task(
                name = task_name,
                start_date = datetime.strftime(datetime.now(),'%Y-%m-%d'),
                end_date = datetime.strftime(datetime.now(),'%Y-%m-%d'),
                weightage = 1,
                priority = 'High',
                assigned_to = '',
                status = 'New',
                estimated_hrs = quotted_hours,
                description = task_name,
                assigned_by = '',
                mid_id = mid.id,
                pid_id = pid,
                quotted_hours = quotted_hours
            )
            task.save()
    return JsonResponse({'status':"OK",'id':pid})


# ********************              Analysis           ***************************#


# Self Timesheet Analysis
@login_required(login_url='home')
@unathenticated
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def timesheet_analysis(request):
    return render(request,'timesheet_analysis.html',{"module":"analysis"}) 

@csrf_exempt
@login_required(login_url='home')
@unathenticated
def getTimesheetLogs(request):
    from_date = datetime.strftime( datetime.now(),'%Y-%m-01')
    to_date = datetime.strftime( datetime.now(),'%Y-%m-%d')
    if request.method =='POST':
        from_date =request.POST['from_date']
        to_date  =request.POST['to_date']
        id = request.POST.get('id')
        mode = request.POST['mode']
        if mode == 'edit_timesheetlog':
            hours = request.POST.get('hours')
            if hours.__contains__(':'):
                duration = timedelta(hours=int(hours.split(':')[0]),minutes=int(hours.split(':')[1])).total_seconds()
            else:
                duration = timedelta(hours=int(hours.split(':')[0])).total_seconds()
            timesheet_ = timesheet_submission.objects.get(id = id)
            timesheet_.date = request.POST.get('date')
            timesheet_.hours = duration
            timesheet_.comment = request.POST.get('comment')
            timesheet_.save()
        if mode == 'delete_timesheetlog':
            timesheet_submission.objects.get(id = id).delete()
    daily_data,total_hrs,timeSheet_logs= timesheet_daily_hours(from_date,to_date,request.user.username)
    project_hour = project_hours(from_date,to_date,request.user.username)

    return JsonResponse({'to_date':to_date,'from_date':from_date,'pieData':project_hour,'xyData':daily_data,
                        'totalWorkedHours':total_hrs,'logs':timeSheet_logs})

def project_hours(from_date,to_date,username):
    project_hours=list(timesheet_submission.objects
                .values('task_id__pid__name')
                .filter(date__range=[from_date, to_date],uid__username = username)
                .order_by('task_id__pid__name')
                .annotate(total_hrs = Sum('hours')))
    for i in project_hours:
        i['total_hrs'] = float(secondToHours(i['total_hrs'])[:-3].replace(":","."))
    return project_hours

def timesheet_daily_hours(from_date,to_date,username):
    daily_hours =list(timesheet_submission.objects 
            .filter(date__range=[from_date, to_date],uid__username = username)  
            .annotate(day = Cast(ExtractDay('date'),CharField()))
            .annotate(message = Concat('task_id__pid__name',V('-'),'hours',V('hrs'),output_field=CharField()))
            .annotate(_pro_name = GroupConcat('message',output_field=CharField()))
            .values('day','_pro_name')                      
            .order_by('date')                                    
            .annotate(total_hrs = Sum('hours'))) 
    for i in daily_hours:
        i['total_hrs'] = float(secondToHours(i['total_hrs'])[:-3].replace(":","."))
        
    total_hrs = timesheet_submission.objects.filter(date__range=[from_date, to_date],uid__username = username) .aggregate(hrs = Sum('hours')) 
    total_hrs['hrs'] =secondToHours(total_hrs['hrs'])[:-3]

    timeSheet_logs = list(timesheet_submission.objects           
                        .filter(date__range=[from_date, to_date],uid__username = username)  
                        .order_by('-date')
                        .annotate(total_hrs = Sum('hours'))
                        .values('task_id__pid__name','task_id__mid__name','task_id__pid__name','task_id__name','date','hours','comment','id'))
    for i in timeSheet_logs:
        i['hours'] = secondToHours(i['hours'])[:-3]
    return daily_hours,total_hrs,timeSheet_logs

# Overall time analysis validation
@csrf_protect
@login_required(login_url='home')
@unathenticated
def allTimesheetLog(request):
    if request.user.role != "Employee":
        return render(request,'timesheet_log.html',{"module":"timesheet"})  
    return HttpResponse("Sorry!! You are not Authorized")
    
@csrf_exempt
def get_summary_template(request):
    year = datetime.today().year
    week = datetime.today().strftime("%V")
    d = str(year)+'-'+ week

    # week_start_date =datetime.strptime(d + '-1', "%Y-%W-%w") # week start from Monday
    # week start from Saturday
    if  datetime.today().weekday()>= 5:
        week_start_date =datetime.strptime(d + '-1', "%Y-%W-%w") + timedelta(days=5) 
    else: 
        week_start_date =datetime.strptime(d + '-1', "%Y-%W-%w") - timedelta(days=2) 

    week_end_date =week_start_date + timedelta(days=6)
    week_days = [d.strftime('%Y-%m-%d') for d in pd.date_range(week_start_date, periods=7) ]#date.today()
    if request.method == 'POST':
        employee_id = request.POST.get('empl_id')
        presentweek_start_date = datetime.strptime(request.POST.get('fromdate_'),'%d-%b-%Y')
        mode = request.POST.get('mode')
        if mode=='accept':
            week_start_date = presentweek_start_date
            week_end_date = presentweek_start_date +  timedelta(days=6)
            week_days = [d.strftime('%Y-%m-%d') for d in pd.date_range(presentweek_start_date, periods=7) ]
            for day in week_days:
                timeshhetsubmissio_id=timesheet_submission.objects.values('id').filter(Q(uid = employee_id) & Q(date= day))
                if timeshhetsubmissio_id:
                    for day_i in timeshhetsubmissio_id:
                        update_submission = timesheet_submission.objects.get(pk=day_i['id'])
                        update_submission.submission_status="Accepted"
                        update_submission.save()
        elif mode=='view_projectlist':
            week_start_date = presentweek_start_date
            week_end_date = presentweek_start_date +  timedelta(days=6)
            empweek_hrs = timesheet_submission.objects.values('task_id__pid__name','task_id__mid__name','task_id__name').filter(Q(date__range=[week_start_date,week_end_date]) 
            & Q(uid=employee_id)).annotate(Week_hours = Sum('hours'))
            for idx, x in enumerate(empweek_hrs):
                empweek_hrs[idx]['Week_hours']=secondToHours(x["Week_hours"])[:-3]
            return JsonResponse({'empweek_hrs':list(empweek_hrs)})
        elif mode=='detailed_view':
            data =[]
            week_days = [d.strftime('%Y-%m-%d') for d in pd.date_range(presentweek_start_date, periods=7) ]
            week_start_date = presentweek_start_date
            week_end_date = presentweek_start_date +  timedelta(days=6)
            task_lists = timesheet_submission.objects.values('task_id','task_id__pid__name','task_id__mid__name','task_id__name','date','hours').filter(Q(uid = employee_id) 
                                                            & Q(date__range=[week_start_date,week_end_date])).order_by('task_id')
            taskIDtemp = 0                                                        
            for task in task_lists:
                if taskIDtemp !=task['task_id']:
                    taskIDtemp =task['task_id']
                    row_data = [task['task_id__pid__name'], task['task_id__mid__name']+' : '+task['task_id__name']]
                    for day in week_days:
                        if day == str(task['date']):
                            row_data.append(str(timedelta(seconds=task['hours']))[:-3].replace(':','.'))
                            taskIDtemp = task['task_id'] 
                            data.append(row_data) 
                        else:
                            row_data.append('')
                else:
                    for indx,day in enumerate(week_days):
                        if day == str(task['date']):
                            data[len(data) - 1][indx + 2] = str(timedelta(seconds=task['hours']))[:-3].replace(':','.')
                            taskIDtemp = task['task_id'] 
                            break
            tableHeader =['Task'] +[datetime.strftime(d,'%a-%d') for d in pd.date_range(presentweek_start_date, periods=7)]
            submittedUser = CustomEmployeeDetails.objects.get(pk=employee_id)
            reporting_to_ = CustomEmployeeDetails.objects.values('first_name').filter(username = submittedUser.reporting_to)
            return JsonResponse({'emp_deailed_data':list(data),'week_days':list(tableHeader),'reporting_to':reporting_to_[0]['first_name']})
        elif mode=='postdate':
            week_start_date = presentweek_start_date  +  timedelta(days=7)
            week_end_date = presentweek_start_date +  timedelta(days=13)
        elif mode=='predate': 
            week_start_date = presentweek_start_date  - timedelta(days=7)
            week_end_date = presentweek_start_date -  timedelta(days=1)
        else:
            week_start_date = presentweek_start_date
            week_end_date = presentweek_start_date +  timedelta(days=6)
            update_submission_id = timesheet_submission.objects.values('id').filter(Q(date__range=[week_start_date,week_end_date])& Q(uid=employee_id))
            
            for status in update_submission_id:
                update_submission = timesheet_submission.objects.get(pk=status['id'])
                update_submission.submission_status='Rejected'
                update_submission.save()
    # Rejected Mail 
            uid = CustomEmployeeDetails.objects.get(pk=employee_id)
            subject = 'Timesheet not accepted'
            text_content = "This is an important message."
            html_content = rejectionMessageBody(uid.first_name,year,week,week_start_date.date(),week_end_date.date())
            msg = EmailMultiAlternatives(subject,text_content,"icproprojects@gmail.com",[uid.email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
    
    tabledata = CustomEmployeeDetails.objects.values('first_name','id').filter(is_active =True).order_by('first_name').exclude(groups__name__in = ['Human Resources']) if request.user.groups.filter(name = 'Human Resources').exists() else CustomEmployeeDetails.objects.values('first_name','id').filter(Q(reporting_to=request.user.username)& Q(is_active=True)).order_by('first_name')
   
    if tabledata:
        for i in tabledata:
            data =timesheet_submission.objects.values('submission_status').annotate(Week_hours=Sum('hours')).filter(Q(date__range=[week_start_date,week_end_date]) & Q(uid_id=i['id']))
            if data:
                data[0]['submission_status'] = data[0]['submission_status'] if data[0]['submission_status'] else "NotSubmitted"
                i.update(data[0])    
            else:
                i.update({'submission_status': "NotSubmitted", 'Week_hours': None})

    if tabledata:
        for idx, x in enumerate(tabledata):
            tabledata[idx]['Week_hours']=secondToHours(x["Week_hours"])[:-3] if x["Week_hours"] else '00.00'
   
    return JsonResponse({'tabledata':list(tabledata),'weeknum':week_start_date.strftime("%V"),
                                        "week_start_date":datetime.strftime(week_start_date,'%d-%b-%Y'),
                                        "week_end_date":datetime.strftime(week_end_date,'%d-%b-%Y')})

# Overall time analysis validation
@csrf_protect
@login_required(login_url='home')
@unathenticated
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def OverallTimesheetLog(request):
    if request.user.role != "Employee":
        dept_groups = request.user.groups.values_list('name',flat = True)

        from_date = datetime.strftime(datetime.now(),'%Y-%m-01')

        to_date =datetime.strftime(datetime.now(),'%Y-%m-%d')

        pro_name = Projects.objects.filter(department__in = dept_groups).values('name')

        emp_name = CustomEmployeeDetails.objects.filter(groups__name__in = dept_groups.exclude(name="General")).values('first_name').distinct().order_by('first_name')

        args = {'task_id__pid__department__in' :dept_groups}

        selectedProject = request.POST.get('project')

        selectedEmpolyee = request.POST.get('Empname')

        if request.method == 'POST':    
            from_date = request.POST.get('from_date')
            to_date  = request.POST.get('to_date') 
            if selectedProject:
                if selectedEmpolyee:
                    args['task_id__pid__name'] = selectedProject
                    args['uid__first_name'] = selectedEmpolyee
                else:
                    args['task_id__pid__name'] =selectedProject
            elif selectedEmpolyee:
                args['uid__first_name'] = selectedEmpolyee
        args['date__range'] = [from_date, to_date]

        logs = list(timesheet_submission.objects.values('task_id__pid__name','uid__first_name','date','comment','task_id__mid__name')
                    .filter(**args)
                    .order_by('date')
                    .annotate(total_hrs = Sum('hours')))                   
        for i in logs:
            i['total_hrs'] = secondToHours( i['total_hrs'])[:-3]
        return render(request,'overall_timsheet_log.html',{"module":"analysis",'logs':(logs),'from_date':from_date,'to_date':to_date,
                                                           'selectedProject':selectedProject,'selectedEmpolyee':selectedEmpolyee,'pro_name':pro_name,'emp_name':emp_name})
    
    return HttpResponse("Sorry!! You are not Authorized")

##Employee month hrs analysis
@csrf_protect
@login_required(login_url='home')
@unathenticated
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def employee_month_hrs(request):
    dept_groups = request.user.groups.values_list('name',flat = True).exclude(name="General")
    from_date = datetime.strftime(datetime.now(),'%Y-%m-01')
    to_date = datetime.strftime(datetime.now(),'%Y-%m-%d') 
    if request.method == 'POST':
        from_date = request.POST.get('from_date')
        to_date  = request.POST.get('to_date') 

    args = {'date__range':[from_date, to_date],'task_id__pid__department__in' :dept_groups}

    data =list(timesheet_submission.objects 
                .filter(**args)
                .values('uid__first_name').annotate(total_hrs = Sum('hours')).order_by('-uid__first_name'))
    for i in data:
        i['total_hrs'] = float(secondToHours( i['total_hrs'])[:-3].replace(":","."))
    return render(request,'employee_month_analysis.html',{"module":"analysis",'data':data,'from_date':from_date,'to_date':to_date})

# Employee Analysis
@csrf_protect
@login_required(login_url='home')
@unathenticated
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def allTimesheetAnalysis(request):
    dept_list = request.user.groups.values_list('name',flat = True).exclude(name="General")#Group.objects.values('name')
    from_date = datetime.strftime(datetime.now(),'%Y-%m-01')
    to_date =datetime.strftime(datetime.now(),'%Y-%m-%d')

    selectedProject = request.POST.get('project')

    active = request.POST.get('active',False)

    args = {'date__range':[from_date, to_date],'task_id__pid__department__in' :dept_list}
    
    project_List =list(timesheet_submission.objects.values("task_id__pid__name")
                       .filter(**args)
                       .order_by('task_id__pid__name').distinct())
   
    pro_name = Projects.objects.filter(department__in= dept_list).values('name').order_by('name')

    Result =[]
    temp =[]
    emp_name =""
    emp_name_temp =""
    checked = True
    if request.method == 'POST':    
        from_date =request.POST['from_date']
        to_date  =request.POST['to_date'] 
        if selectedProject:
            args['task_id__pid__name'] =selectedProject

        args['date__range']=[from_date, to_date]

    data = list(timesheet_submission.objects
                .values('uid__first_name','task_id__pid__name')
                .filter(**args)
                .order_by('uid__first_name')
                .annotate(total_hrs = Sum('hours')))
    
    for item in data:
        emp_name_temp =item["uid__first_name"]
        if emp_name == emp_name_temp:
            Result[len(Result)-1][item["task_id__pid__name"]] =float(secondToHours( item['total_hrs'])[:-3].replace(":","."))
        else:
            temp = [{"uid__first_name": item["uid__first_name"],item["task_id__pid__name"]:float(secondToHours( item['total_hrs'])[:-3].replace(":","."))}]
            emp_name =emp_name_temp
            Result = list(chain(Result, temp))
            Result[len(Result)-1]["none"] = 0  
    return render(request,'all-timesheet-analysis.html',{"module":"analysis",'data':(Result),'from_date':from_date,'to_date':to_date,
                                                         'selectedProject':selectedProject,'pro_name':pro_name,'project_List':project_List,'checked':checked})

#Task Analysis
@csrf_protect
@login_required(login_url='home')
@unathenticated
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def task_analysis(request):
    dept_list = request.user.groups.values_list('name',flat = True).exclude(name="General") #Group.objects.values('name')
    
    from_date = datetime.strftime(datetime.now(),'%Y-%m-01')

    to_date = datetime.strftime(datetime.now(),'%Y-%m-%d')

    selectedEmpolyee   = request.POST.get('Empname')

    selectedProject   = request.POST.get('project')
    
    employees = list(CustomEmployeeDetails.objects.filter(groups__name__in =dept_list)
                .values('first_name').order_by('first_name').distinct())
    
    projetcs = list(Projects.objects.filter(department__in= dept_list)
                .values('name').order_by('name'))
    args = {'task_id__pid__department__in' :dept_list}
   
    if request.method == 'POST':    
        from_date = request.POST.get('from_date')
        to_date  = request.POST.get('to_date') 
        if selectedProject:
            if selectedEmpolyee:
                args['task_id__pid__name'] = selectedProject
                args['uid__first_name'] = selectedEmpolyee
            else:
                args['task_id__pid__name'] =selectedProject
        elif selectedEmpolyee:
            args['uid__first_name'] = selectedEmpolyee
    args['date__range'] = [from_date, to_date]
            
    data = list(timesheet_submission.objects
                .values('task_id__name').filter(**args) 
                .order_by('task_id__name')
                .annotate(total_hrs = Sum('hours')))  
    for i in data:
        i['total_hrs'] = float(secondToHours( i['total_hrs'])[:-3].replace(":","."))
    return render(request,'Task_Analysis.html',{"module":"analysis",'data':(data),'from_date':from_date,'to_date':to_date,
                                                'selectedProject':selectedProject,'selectedEmpolyee':selectedEmpolyee,'emp_name':employees,'pro_name':projetcs})

#Project Analysis
@csrf_protect
@login_required(login_url='home')
@unathenticated
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def allProjectAnalysis(request):
    dept_list = request.user.groups.values_list('name',flat = True).exclude(name="General")
    from_date = datetime.strftime(datetime.now(),'%Y-%m-01')
    to_date = datetime.strftime(datetime.now(),'%Y-%m-%d')
    
    args = {'task_id__pid__department__in' :dept_list}

    employee_List =list(timesheet_submission.objects
                        .values("uid__first_name")
                        .filter(**args)
                        .order_by('uid__first_name').distinct())
    
    employee_Listingroup = list(CustomEmployeeDetails.objects.filter(groups__name__in = dept_list,is_active= True)
                .values('first_name').order_by('first_name').distinct())
    # active = request.POST.get('active',True)
    selectedEmpolyee = request.POST.get('Empname')

    Result =[]
    temp =[]
    pro_name =""
    pro_name_temp =""
    if request.method == 'POST':    
        from_date =request.POST['from_date']
        to_date  =request.POST['to_date']  
        if selectedEmpolyee:
            args['uid__first_name'] =selectedEmpolyee
    args['date__range']=[from_date, to_date]
            
    data = list(timesheet_submission.objects
                .values('uid__first_name','task_id__pid__name')
                .filter(**args)
                .order_by('task_id__pid__name')
                .annotate(total_hrs = Sum('hours'))) 
          
    for item in data:
        pro_name_temp =item["task_id__pid__name"]
        if pro_name == pro_name_temp:
            Result[len(Result)-1][item["uid__first_name"]] =float(secondToHours( item['total_hrs'])[:-3].replace(":","."))
        else:
            temp = [{"task_id__pid__name": item["task_id__pid__name"],item["uid__first_name"]:float(secondToHours( item['total_hrs'])[:-3].replace(":","."))}]
            pro_name =pro_name_temp
            Result = list(chain(Result, temp))
            Result[len(Result)-1]["none"] = 0

    return render(request,'all-project-analysis.html',{"module":"analysis",'data':(Result),'selectedEmpolyee':selectedEmpolyee,
                                                       'from_date':from_date,'to_date':to_date,'employee_List':employee_List,
                                                       'employee_Listingroup':employee_Listingroup})  
    
#Task/Employee Analysis 
@csrf_protect   
@login_required(login_url='home')
@unathenticated
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def task_employee_analysis(request):
    dept_list = request.user.groups.values_list('name',flat = True).exclude(name="General")
    from_date = datetime.strftime(datetime.now(),'%Y-%m-01')
    to_date =datetime.strftime(datetime.now(),'%Y-%m-%d')

    selctedTask = request.POST.get('task') 

    args = {'task_id__pid__department__in' :dept_list}

    task_list = list(timesheet_submission.objects
                    .values("task_id__name")
                    .filter(**args)
                    .order_by('task_id__name').distinct())           
    Result =[]
    temp =[]
    emp_name =""
    emp_name_temp =""
    if request.method == 'POST':    
        from_date =request.POST.get('from_date')
        to_date  = request.POST.get('to_date')
        if selctedTask:
            args['task_id__name'] =selctedTask
    args['date__range'] =[from_date, to_date]

    data = list(timesheet_submission.objects
                .values('task_id__name','uid__first_name')
                .filter(**args)
                .order_by('uid__first_name')
                .annotate(total_hrs = Sum('hours')))
    for item in data:
        emp_name_temp =item["uid__first_name"]
        if emp_name == emp_name_temp:
            Result[len(Result)-1][item["task_id__name"]] = float(secondToHours( item['total_hrs'])[:-3].replace(":","."))
        else:
            temp = [{"uid__first_name": item["uid__first_name"],item["task_id__name"]:float(secondToHours( item['total_hrs'])[:-3].replace(":","."))}]
            emp_name =emp_name_temp
            Result = list(chain(Result, temp))
            Result[len(Result)-1]["none"] =0
    
    return render(request,'task_vs_employee_analysis.html',{"module":"analysis",'data':(Result),
                                                            'from_date':from_date,'to_date':to_date,
                                                            'task_list':task_list,'selctedTask':selctedTask})

#Department analysis
@csrf_protect
@login_required(login_url='home')
@unathenticated
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def dept_analysis(request):
    from_date = datetime.strftime(datetime.now(),'%Y-%m-01')
    to_date = datetime.strftime(datetime.now(),'%Y-%m-%d') 
    dept_list = request.user.groups.values_list('name',flat = True).exclude(name="General")

    setectedDept =request.POST.get('department')
    
    args = {'task_id__pid__department__in' :dept_list}

    if request.method == 'POST':
        from_date =request.POST['from_date']
        to_date = request.POST['to_date']    
        if setectedDept:
            args['task_id__pid__department'] =setectedDept
    args['date__range'] =[from_date, to_date]

    Result=[]

    data = list(timesheet_submission.objects 
                .filter(**args).order_by('date')
                .values('date').annotate(total_hrs = Sum('hours')))
    for day in data:
        temp  = [{"Day" : day['date'].strftime('%Y-%m-%d'),"total_hrs":float(secondToHours( day['total_hrs'])[:-3].replace(":","."))}]
        Result = list(chain(Result, temp))

    return render(request,'Department_Analysis.html',{"module":"analysis",'data':Result,'dept_list':dept_list,'setectedDept':setectedDept,
                                                      'from_date':from_date,'to_date':to_date,})

# Time Budget analysis

#Efficiency
@csrf_protect
@login_required(login_url='home')
@unathenticated
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def timeBudgetAnalysis(request):
    data = Projects.objects.values('name','id').annotate(bdg_hrs=Sum('task__quotted_hours'))
    actualHours = {}

    for i in timesheet_submission.objects.values('task_id__pid').annotate(act_hrs=Sum('hours')):
        actualHours[i['task_id__pid']] = secondToHours(i['act_hrs'])[:-6].replace(":",".")
    for i in data:
        i['act_hrs'] = actualHours[i['id']] if i['id'] in actualHours else 0
        if not i['bdg_hrs']:
            i['bdg_hrs'] = 0
    return render(request,'time_budget_analysis.html',{"module":"analysis",'data':list(data)})

def secondToHours(seconds):
    if seconds and seconds!=0:
        h, m, s = map(lambda x: int(x), [seconds/3600, seconds%3600/60, seconds%60])
        return f'{h}.{m:02d}.{s:02d}'
    return f'{00}.{00}'

# Email Scheduling
def emailsend(request):
    year = datetime.today().year
    week = datetime.today().strftime("%V")
    d = str(year)+'-'+ week

    # week_start_date =datetime.strptime(d + '-1', "%Y-%W-%w") # week start from Monday  ['1000','1001','9001','9003','9901'] + 
    if  datetime.today().weekday()>= 5:
        week_start_date =datetime.strptime(d + '-1', "%Y-%W-%w") + timedelta(days=5) 
    else: 
        week_start_date =datetime.strptime(d + '-1', "%Y-%W-%w") - timedelta(days=2) 

    week_end_date =week_start_date + timedelta(days=6)

    excludeList =list(timesheet_submission.objects.values_list('uid__username',flat = True)
                                                                .filter(date__range =[week_start_date,week_end_date],
                                                                        submission_status__isnull = False).distinct()) 

    data =list(CustomEmployeeDetails.objects.values('first_name','email').annotate(
                                            _reportingto= Subquery(CustomEmployeeDetails.objects.values('email')
                                                                .filter(username =OuterRef('reporting_to')))
                                            ).exclude(Q(username__in = excludeList)).filter(Q(is_active=True) & ~Q(groups__name__in =["Admin","Human Resources"])))
    
    return JsonResponse({"result":data,'year':year,'week':week 
                         ,'week_start_date':week_start_date.date(),'week_end_date':week_end_date.date()})

# Timesheet rejection mail body
def rejectionMessageBody(name,year,week,fromDate,toDate):
    html="""
            <body>
                <p>Dear %s ,<br><br>
                <h5 style="color: orange;">Timesheet has not accepted</h5>
                This email is to inform you that your timesheet for the following week has not accepted.
                    <br>
                    Year:%s , week:%s , Period: %s - %s
                    <br><br>
					Best regards,
                    <br>
					IC Pro solutions Pvt Ltd.
                    </p>
                </body>
        """
    return html%(name,year,week,fromDate,toDate)

