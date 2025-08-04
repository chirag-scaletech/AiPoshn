from django.contrib import admin

from myapp.models import Teacher

class TeacherAdmin(admin.ModelAdmin):
    list_display = ('id', 'username_en', 'username_gu')

# Register your models here.
admin.site.register(Teacher, TeacherAdmin)

