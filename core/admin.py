from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from authentication.models import User, Department, Course, Student, Staff
from .models import ClassSchedule, Attendance, Session

# Register Core models
admin.site.register(ClassSchedule)
admin.site.register(Attendance)
admin.site.register(Session)

# Optional: Add custom admin classes for more control
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ('course', 'instructor', 'get_day_display', 'start_time', 'end_time', 'room', 'session')
    list_filter = ('day_of_week', 'course', 'instructor', 'session')
    search_fields = ('course__name', 'course__code', 'instructor__user__username', 'room')
    
    def get_day_display(self, obj):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[obj.day_of_week]
    
    get_day_display.short_description = 'Day'

# admin.site.register(ClassSchedule, ClassScheduleAdmin)  # Uncomment to use the custom admin class