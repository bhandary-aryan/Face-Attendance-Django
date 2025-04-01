from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from .models import User, Department, Course, Student, Staff

# Register main models
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type')
    list_filter = ('user_type',)
    search_fields = ('username', 'email', 'first_name', 'last_name')

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department')
    list_filter = ('department',)
    search_fields = ('code', 'name')

class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'get_full_name', 'department')
    list_filter = ('department',)
    search_fields = ('student_id', 'user__first_name', 'user__last_name')
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Name'

class StaffAdmin(admin.ModelAdmin):
    list_display = ('staff_id', 'get_full_name', 'department')
    list_filter = ('department',)
    search_fields = ('staff_id', 'user__first_name', 'user__last_name')
    filter_horizontal = ('courses',)
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Name'

# Register all models with their custom admin classes
admin.site.register(User, UserAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Staff, StaffAdmin)

# Fix LogEntry to use custom user model
# This step ensures that the admin logs work with your custom user model
LogEntry._meta.get_field('user').remote_field.model = User

# Optional: If you want to see admin logs in the admin interface
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag')
    list_filter = ('action_time', 'user', 'content_type')
    search_fields = ('object_repr', 'change_message')
    date_hierarchy = 'action_time'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(LogEntry, LogEntryAdmin)