from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

class CustomEmployeeDetails(AbstractUser):
    phone = models.CharField(max_length=10,null=True,default="None")
    designation = models.CharField(max_length=30)
    role = models.CharField(max_length=30)
    reporting_to = models.CharField(max_length=30,null=True)

    def __str__(self) :
        return self.username

    
