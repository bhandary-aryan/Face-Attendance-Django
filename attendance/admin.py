from django.contrib.admin import AdminSite, ModelAdmin
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from core.models import Student, Attendance

class StudentAdmin(ModelAdmin):
    list_display = ('id', 'name', 'department')
    list_filter = ('department',)
    search_fields = ('name', 'department')

class AttendanceAdmin(ModelAdmin):
    list_display = ('student', 'date', 'status')
    list_filter = ('date', 'status')
    search_fields = ('student__name',)
    date_hierarchy = 'date'

class CustomAdminSite(AdminSite):
    site_header = 'Face Attendance Administration'
    site_title = 'Face Attendance Admin'
    index_title = 'Dashboard'

    def index(self, request, extra_context=None):
        # Get total students count
        total_students = Student.objects.count()
        
        # Calculate attendance rate for the current month
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        attendance_count = Attendance.objects.filter(date__gte=start_of_month).count()
        working_days = (now - start_of_month).days
        attendance_rate = (attendance_count / (total_students * working_days)) * 100 if working_days > 0 else 0
        
        # Get monthly attendance data for the chart
        months = []
        present_data = []
        absent_data = []
        
        for i in range(12):
            month_start = now.replace(day=1) - timedelta(days=30*i)
            month_end = month_start.replace(day=1) + timedelta(days=32)
            month_end = month_end.replace(day=1) - timedelta(days=1)
            
            monthly_attendance = Attendance.objects.filter(
                date__gte=month_start,
                date__lte=month_end
            ).count()
            
            total_possible = total_students * (month_end - month_start).days
            present = monthly_attendance
            absent = total_possible - present if total_possible > present else 0
            
            months.insert(0, month_start.strftime('%b'))
            present_data.insert(0, present)
            absent_data.insert(0, absent)
        
        # Get department-wise attendance stats
        departments = Student.objects.values('department').annotate(
            count=Count('id')
        ).order_by('-count')
        
        department_stats = []
        for dept in departments[:4]:  # Top 4 departments
            dept_students = Student.objects.filter(department=dept['department'])
            dept_attendance = Attendance.objects.filter(
                student__in=dept_students,
                date__gte=start_of_month
            ).count()
            
            total_possible = dept['count'] * working_days
            attendance_percentage = (dept_attendance / total_possible * 100) if total_possible > 0 else 0
            
            department_stats.append({
                'name': dept['department'],
                'percentage': round(attendance_percentage, 1)
            })
        
        context = {
            'total_students': total_students,
            'attendance_rate': round(attendance_rate, 1),
            'months': months,
            'present_data': present_data,
            'absent_data': absent_data,
            'department_stats': department_stats,
        }
        
        if extra_context:
            context.update(extra_context)
            
        return super().index(request, context)

admin_site = CustomAdminSite(name='custom_admin')
admin_site.register(Student, StudentAdmin)
admin_site.register(Attendance, AttendanceAdmin) 