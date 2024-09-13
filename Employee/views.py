from itertools import chain
from django.shortcuts import render,redirect
from django.contrib.auth import login, authenticate,logout
from django.contrib.auth.models import User,Group
from django.db.models import Q,Sum,OuterRef, Subquery
from .models import CustomEmployeeDetails
from .forms import CustomEmployeeDetailsForm
from django.contrib.auth.decorators import login_required
from django. views. decorators. csrf import csrf_exempt
from django.contrib import messages
from .decorators import unathenticated,allowedGroups
from django.http.response import HttpResponse, JsonResponse
from django.views.decorators.cache import cache_control
from django.db.models import F


@csrf_exempt
def loginUser(request):
    if request.method == 'POST':
        Username = request.POST.get('username')
        Password = request.POST.get('password')
        user = authenticate(username=Username, password=Password)
        if user is not None:
            login(request,user)
            return redirect('index')
        else:
            messages.error(request, 'Invalid credentials...!')
            return redirect('home')

@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='home')
def index(request):
    return render(request,'home.html',{"module":"home"})

@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='home')
def signup(request): 
    if request.method == 'POST':
        form = CustomEmployeeDetailsForm(request.POST)
        if form.is_valid():
            user = form.save()
            for groupname in request.POST.getlist('department'):
                my_group  = Group.objects.get(name = groupname)
                user.groups.add(my_group)
            return redirect('getUsers')
        else:
            return JsonResponse({"formError":form.errors.as_json()})

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@allowedGroups(allowedgroup=['Admin','Software'])
def employeeDetails(request):
    if request.user.role != "Employee":
        return render(request, 'employee_details.html',{"module":"usermanagement"})
    return HttpResponse("Sorry!! You are not Authorized")

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def editEmployee(request):
    if request.method == "POST":
        id = request.POST.get('id')
        user = CustomEmployeeDetails.objects.get(id = id)
        user.first_name = request.POST.get('first_name')
        user.role = request.POST.get('role')
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.reporting_to = request.POST.get('reporting_to')
        user.phone = request.POST.get('phone')
        user.designation = request.POST.get('designation')
        if request.POST.get('is_active') == "on":
            user.is_active = True
        else:
            user.is_active = False
        user.save(update_fields=['first_name','role','username','username','email','reporting_to','phone','is_active','designation'])

        user.groups.clear()
        for groupname in request.POST.getlist('department'):
                my_group  = Group.objects.get(name = groupname)
                user.groups.add(my_group)
        return redirect('getUsers')

@csrf_exempt
@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def getUsers(request):
    users =list(CustomEmployeeDetails.objects.filter(is_active =True).values().order_by('first_name'))
    if request.method == 'POST':
        state = True  if request.POST.get('checked') == "true" else False
        users =list(CustomEmployeeDetails.objects.filter(is_active =state).values().order_by('first_name'))
    for user in users:
        user['departments'] = list(CustomEmployeeDetails.objects.get(pk=user['id']).groups.values_list('name',flat=True))
    
    return JsonResponse({"users":users})

@login_required(login_url='home')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def deleteEmployee(request):
    CustomEmployeeDetails.objects.get(id = request.POST.get('id')).delete()
    return redirect('getUsers')
