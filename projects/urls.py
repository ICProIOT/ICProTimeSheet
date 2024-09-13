from os import name
from django.urls import path,reverse_lazy

from . import views 
from timeline import views as timeline_views

urlpatterns = [

#Projects Related   
    path('', views.createProject, name='create-project'),
    path('list-projects/', views.listProjects, name='list-projects'),
    path('edit-project/', views.editProject, name='edit-project'),
    path('delete-project/<int:id>/', views.deleteProject, name='delete-project'),

    path('task-manager/<int:id>/', views.taskManager, name='task-manager'),
 # Milestone
    path('create-milestone/<int:id>/', views.createMilestone, name='create-milestone'),
    path('edit-milestone/<int:pid>/', views.editMilestone, name='edit-milestone'),
    path('delete-milestone/<int:id>/<int:pid>/', views.deleteMilestone, name='delete-milestone'),
# Task
    path('create-task/<int:pid>/', views.createTask, name='create-task'),
    path('editTaskAjax', views.editTaskAjax, name='editTaskAjax'),
    path('delete-task/<int:id>/<int:mid>/<int:pid>/', views.deleteTask, name='delete-task'),

    path('resourceplanning',views.resourceplanning ,name='resourceplanning'),
    path('ajax/getPlandetails',views.getPlandetails ,name='getPlandetails'),

# gantchart
    path('gantchart-filter',views.gantchartdatefilter, name='gantchart-filter'),
    
    path('task_summary/',views.task_summary,name='task_summary'),
    path('loadtasksummary_table',views.loadtasksummary_table,name='loadtasksummary_table'),
    path('creatreTaskAjax', views.creatreTaskAjax, name='creatreTaskAjax'),
    path('create_task_using_mtemplate',views.create_task_using_mtemplate,name='create_task_using_mtemplate'),

# Edit templates
    path('Add-milestone/',views.add_milestone,name='Add-milestone'),
    path('Add-task/',views.add_task,name='Add-task'),
    path('list-templates/', views.list_templates, name='list-templates'),
    path('ajax/listtemplate_task',views.listtemplate_task ,name='listtemplate_task'),  
    path('delete-milestone_templates/<int:id>/',views.delete_milestone_template,name ='delete-milestone_templates'),
    path('delete-task_templates/<int:id>/<int:mid>/',views.delete_task_templates,name ='delete-task_templates'),
    path('Edit_Load_templates/<int:id>/',views.Edit_Load_templates,name='Edit_Load_templates'),

    #  checklist
    path('create-checklist/',views.create_checklist,name='create-checklist'),
    path('list-checklist/',views.list_checklist,name='list-checklist'),
    path('check-checklist-name',views.validate_checklist_name,name='check-checklist-name'),
    path('edit-checklist/<int:checklist_id>',views.edit_checklist_details,name='list-checklist'),
    path('get-checklist/<int:pid>',views.get_project_checklist,name='get-checklist'),
    path('get-checklist/',views.add_checklist_to_project,name='set-checklist'),
    path('checklist/<int:checklist_id>/',views.edit_checklist,name='edit-checklist'),
    path('delete-checklist/<int:checklist_id>/', views.delete_checklist, name='delete-checklist'),

    #questions

    path('checklist/<int:p_id>/<int:c_id>/',views.view_checklist,name='view-checklist'),
    path('checklist/view-sections/<int:c_id>/<int:s_id>',views.view_sections,name='view-section'),
    path('checklist/validate-section-name',views.validate_section_name,name='validate-section-name'),
    path('checklist/<int:p_id>/<int:c_id>/<int:s_id>',views.get_questions,name='get-questions'),
    path('checklist/validate-question-name',views.validate_question_name,name='validate-section-name'),

    path('checklist/get-question/<int:q_id>',views.get_question,name='get-question'),
    path('checklist/edit-question/<int:c_id>/<int:s_id>/<int:q_id>',views.edit_question,name='edit-question'),
    path('checklist/delete-question/<int:c_id>/<int:s_id>/<int:q_id>',views.delete_question,name='delete-question'),
    path('checklist/delete-section/<int:c_id>/<int:s_id>',views.delete_section,name='delete-section'),
    
    #answer
    path('answer/<int:p_id>/',views.get_project_checklists,name='get-p-checklists'),
    path('answer/<int:p_id>/<int:c_id>/',views.get_checklist_sections,name='get-c-sections'),
    path('answer/<int:p_id>/<int:c_id>/<int:s_id>',views.get_section_questions,name='get-s-questions'),
    path('audit/<int:p_id>/<str:audit>',views.get_project_checklists,name='get-p-checklists'),
    path('audit/<int:p_id>/<int:c_id>/<str:audit>',views.get_checklist_sections,name='get-c-sections'),
    path('audit/<int:p_id>/<int:c_id>/<int:s_id>/<str:audit>',views.get_section_questions,name='get-s-questions'),

    #download attachment
    path('checklist/attachment/<int:question_id>/',views.download_question_attachment, name='download-question-attachment'),
    path('report/download/<int:project_id>/',views.download_project_pdf, name='download-project-pdf'),
    
    
    
]