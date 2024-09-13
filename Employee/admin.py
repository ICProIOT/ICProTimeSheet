from django.contrib import admin
from .models import CustomEmployeeDetails
from .forms import CustomEmployeeDetailsForm
from django.contrib.auth.admin import UserAdmin

# Register your models here.
class CustomEmployeeDetailsAdmin(UserAdmin):
    model = CustomEmployeeDetails
    add_form = CustomEmployeeDetailsForm

    fieldsets = (
        *UserAdmin.fieldsets,(
            'Additional Fields',
            {
                'fields':(
                    'designation',
                    'phone',
                    'role',
                    'reporting_to'
                )
            }
        )

    )

admin.site.register(CustomEmployeeDetails,CustomEmployeeDetailsAdmin)