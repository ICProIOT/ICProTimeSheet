import datetime

from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django.shortcuts import redirect, render
from projects.models import Projects #importing project model from project application
from .forms import document_mange_form,feeds_form,lessonlearnt_form,category_form#,lessonlearntForm  #include the class name which u added in forms
from .models import  category_project, document_manage,feeds,lessonlearnt #include the model name which u have added in models.py
from django. views. decorators. csrf import csrf_exempt
from django.views.decorators.cache import cache_control


# Create your views here.
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def Document_list(request):
    date = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d')
    Documents = document_manage.objects.all()
    return render(request,'document_list.html',{'date':date,'Documents':Documents,'module':'document'})

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def upload(request): 
    if request.method == 'POST':
        form = document_mange_form(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('Documents')
        else:
            return JsonResponse({form.errors})
    else:
        form = document_mange_form()
    return JsonResponse({"Error":'Failed to upload Documents'})

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)   
def delete_document(request,id):
    document_manage.objects.get(pk = id).delete()
    return redirect('Documents')
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def upload_file(request):
    document_id =request.POST.get('id')
    if request.method == "POST":
        form = document_mange_form(request.POST, request.FILES)
        if form.is_valid():
            form_data = form.save(commit=False)
            form_data.id= request.POST.get('id')
            form_data.save()
            return redirect('Documents')
        else:
            return JsonResponse({form.errors})
    else:
        form = document_mange_form()
    return JsonResponse({"Error":'Failed to upload Documents'})
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def feeds_image(request):
    date = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d')
    images = feeds.objects.all()
    if request.method =="POST":
        form = feeds_form(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            images = feeds.objects.all()
            return render(request,'feeds.html',{'date':date,'images':images})
        else:
            return JsonResponse({form.errors})
    else:
        form =feeds_form()        #return JsonResponse({"status":"Error"})
        return render(request,'feeds.html',{'date':date,'images':images})
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def delete_image(request,id):
    feeds.objects.get(pk = id).delete()
    return redirect('feeds')

# New LessonLearnt Page Adding Page
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def lessonlearnts(request):
    
    if request.method=="POST":
        form = lessonlearnt_form(request.POST,request.FILES)
        if form.is_valid():
            form.save()
        return redirect('lesson')
    project_=Projects.objects.all() #taking values from project table
    lessonlearnt_ = lessonlearnt.objects.all() #taking values from lesson learnt table 
    category_=category_project.objects.all().values() #taking values from category table        
    return render(request,'lesson.html',{'project_':project_,'lessonlearnt_':lessonlearnt_,'category_':category_})

# Edit Added LessonLearnt Details
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def edit_lesson(request):
    if request.method == "POST":
        id =  request.POST.get('id')
        lesson_ = lessonlearnt.objects.get(id = id)
        lesson_.Project =  request.POST.get('Project')
        lesson_.Category =  request.POST.get('Category')
        lesson_.Event =  request.POST.get('Event')
        lesson_.Limitations =  request.POST.get('Limitations')
        lesson_.Actions =  request.POST.get('Actions')
        lesson_.Status =  request.POST.get('Status')
        lesson_.Remark =  request.POST.get('Remark')
        lesson_.save(update_fields=['Project','Category','Event','Limitations','Actions','Status','Remark'])
    return redirect('lesson')

# Deleting Added LessonLearnt Details
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def delete_lesson(request,id):
    lessonlearnt.objects.get(pk = id).delete()
    return redirect('lesson')

# Adding New Category Details Page
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def categorys(request):
    if request.method=="POST":
        form = category_form(request.POST)
        if form.is_valid():
            form.save()
    return redirect('lesson')
      
# Delete Added Category Details
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def delete_category(request,id):
    category_project.objects.get(pk = id).delete()
    return redirect('lesson')

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def lesson(request):
    project_=Projects.objects.all() #taking values from project table
    category_= category_project.objects.values().all()
    lesson_ = lessonlearnt.objects.all() #taking values from lesson learnt table 
    if request.method=="POST":
        Project_=request.POST.get('Project')
        Category_=request.POST.get('Category')
        if Project_ == 'All_project' and  Category_== 'All_category':
            lesson_ = lessonlearnt.objects.all() #taking values from lesson learnt table 
        elif Project_ != 'All_project' and  Category_== 'All_category':
            lesson_ = lessonlearnt.objects.filter(Project=Project_).all() #taking values from lesson learnt table 
        elif Project_ == 'All_project' and  Category_!= 'All_category':
            lesson_ = lessonlearnt.objects.filter(Category=Category_).all() #taking values from lesson learnt table 
        else:
            lesson_ = lessonlearnt.objects.filter(Project = Project_,Category = Category_).all() #taking values from lesson learnt table 
    
    return render(request,'lesson.html',{'project_':project_,'lesson_':lesson_,'category_':category_,'module':'document'})
