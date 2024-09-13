from django.urls import path,reverse_lazy

from . import views 

urlpatterns = [
        
    path('login_view', views.loginUser, name='login_view'),  
    path('index/', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
        
    path('getUsers/', views.getUsers, name='getUsers'),
    path('employee-details/', views.employeeDetails, name='employeeDetails'),
    path('edit-employee/', views.editEmployee, name='edit-employee'),
    path('delete-employee/', views.deleteEmployee, name='delete-employee'),
]