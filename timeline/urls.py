from django.contrib import auth
from django.urls import path,reverse_lazy
from django.contrib.auth import views as auth_views
from django.urls.conf import include
from .views import * 
from projects import views as p_views

urlpatterns = [
    # submission
    path('',submission,name="submission"),
    path('ajax/getTimesheetLogs',getTimesheetLogs,name ='getTimesheetLogs'),
    path('get_summary_template',get_summary_template,name='get_summary_template'),


    # Analysis
    path('overall-timesheet-log/',allTimesheetLog,name="All-timesheet-log"),
    path('OverallTimesheetLog/',OverallTimesheetLog, name ='OverallTimesheetLog'),
    path('timesheet_analysis/',timesheet_analysis, name ='timesheet_analysis'),
    path('all-timesheet-analysis/',allTimesheetAnalysis, name= 'all-timesheet-analysis'),
    path('all-project-analysis/',allProjectAnalysis, name= 'all-project-analysis'),
    path('Task_Analysis/',task_analysis, name ='Task_Analysis'),
    path('task_vs_employee_analysis/',task_employee_analysis,name='task_vs_employee_analysis'),
    path('Department_Analysis/',dept_analysis,name='Department_Analysis'),
    path('employee_month_analysis/',employee_month_hrs,name='employee_month_analysis'),
    path('timeBudgetAnalysis/',timeBudgetAnalysis,name='timeBudgetAnalysis'),
    path('ajax/get_time_sheet_templete',submission_templete ,name='get_time_sheet_templete'),

    # project budgeting
    path('time_management',timemanagement,name= 'time_managemnet'),
    path('proj_tabledata',proj_tabledata,name='proj_tabledata'),
    path('template_project/<int:id>/',template_project,name='template_project'),
    path('tabledata_project',tabledata_project,name='tabledata_project'),
    path('edit_tabledata',edit_tabledata,name='edit_tabledata'),

    path('createproject/',p_views.createProject),
    path('getTaskSubmission',getTaskSubmission,name='getTaskSubmission'),
    

    # Email sscheduling
    path('emailsend',emailsend,name='emailsend')

]