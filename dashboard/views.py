from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
import datetime
import json
from django.contrib import messages

from core.models import Attendance, ClassSchedule, Session
from authentication.models import Student, Staff, Course, Department

@login_required
def dashboard_redirect(request):
    """Redirect to appropriate dashboard based on user type"""
    if request.user.user_type == 'admin':
        return redirect('admin_dashboard')
    elif request.user.user_type == 'staff':
        return redirect('staff_dashboard')
    else:
        return redirect('student_dashboard')

@login_required
def attendance_analytics(request):
    """Show attendance analytics dashboard"""
    if request.user.user_type not in ['admin', 'staff']:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard_redirect')
    
    # Filter analytics by department, course, etc.
    department_id = request.GET.get('department')
    course_id = request.GET.get('course')
    
    # Base queryset
    attendance_qs = Attendance.objects.all()
    
    # Apply filters
    if department_id:
        attendance_qs = attendance_qs.filter(
            student__department_id=department_id
        )
    
    if course_id:
        attendance_qs = attendance_qs.filter(
            class_schedule__course_id=course_id
        )
    
    # Staff can only see their own courses
    if request.user.user_type == 'staff':
        try:
            staff = Staff.objects.get(user=request.user)
            attendance_qs = attendance_qs.filter(
                class_schedule__instructor=staff
            )
        except Staff.DoesNotExist:
            pass
    
    # Attendance status distribution
    status_stats = attendance_qs.values('status').annotate(count=Count('id'))
    
    # Attendance by day of week
    day_of_week_stats = attendance_qs.values('class_schedule__day_of_week').annotate(count=Count('id'))
    
    # Attendance by month
    month_stats = []
    current_date = timezone.now().date()
    for i in range(6):  # Last 6 months
        month_start = datetime.date(current_date.year, current_date.month, 1) - datetime.timedelta(days=30*i)
        month_end = (month_start.replace(day=28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)
        
        count = attendance_qs.filter(date__gte=month_start, date__lte=month_end).count()
        month_stats.append({
            'month': month_start.strftime('%b %Y'),
            'count': count
        })
    
    # Attendance rate by course
    course_stats = []
    courses = Course.objects.all()
    if department_id:
        courses = courses.filter(department_id=department_id)
    
    if request.user.user_type == 'staff':
        try:
            staff = Staff.objects.get(user=request.user)
            courses = staff.courses.all()
        except Staff.DoesNotExist:
            pass
    
    for course in courses:
        total_classes = ClassSchedule.objects.filter(course=course).count()
        if total_classes > 0:
            total_attended = attendance_qs.filter(
                class_schedule__course=course,
                status__in=['present', 'late']
            ).count()
            attendance_rate = (total_attended / total_classes) * 100
            course_stats.append({
                'course': course.code,
                'rate': attendance_rate
            })
    
    # Top 10 students by attendance rate
    student_stats = []
    students = Student.objects.all()
    if department_id:
        students = students.filter(department_id=department_id)
    if course_id:
        students = students.filter(courses__id=course_id)
    
    for student in students[:20]:  # Limit to 20 students for performance
        total_classes = ClassSchedule.objects.filter(
            course__in=student.courses.all()
        ).count()
        if total_classes > 0:
            attended_classes = attendance_qs.filter(
                student=student,
                status__in=['present', 'late']
            ).count()
            attendance_rate = (attended_classes / total_classes) * 100
            student_stats.append({
                'student': f"{student.user.first_name} {student.user.last_name}",
                'rate': attendance_rate
            })
    
    # Sort by attendance rate and get top 10
    student_stats = sorted(student_stats, key=lambda x: x['rate'], reverse=True)[:10]
    
    # Get departments and courses for filters
    departments = Department.objects.all()
    
    context = {
        'departments': departments,
        'courses': courses,
        'status_stats': status_stats,
        'day_of_week_stats': day_of_week_stats,
        'month_stats': month_stats,
        'course_stats': course_stats,
        'student_stats': student_stats,
        'selected_department': department_id,
        'selected_course': course_id,
    }
    
    return render(request, 'dashboard/analytics.html', context)

@login_required
def student_attendance_report(request, student_id=None):
    """Show attendance report for a specific student"""
    # If student_id is provided, show that student's report
    # Otherwise, show the logged-in student's report
    
    if student_id:
        if request.user.user_type not in ['admin', 'staff']:
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard_redirect')
        
        student = get_object_or_404(Student, id=student_id)
    else:
        if request.user.user_type != 'student':
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard_redirect')
        
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found.")
            return redirect('dashboard_redirect')
    
    # Get attendance records
    attendance_records = Attendance.objects.filter(
        student=student
    ).select_related('class_schedule', 'class_schedule__course')
    
    # Filter by course
    course_id = request.GET.get('course')
    if course_id:
        attendance_records = attendance_records.filter(
            class_schedule__course_id=course_id
        )
    
    # Filter by date range
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        # Default to first day of current month
        today = timezone.now().date()
        start_date = datetime.date(today.year, today.month, 1)
    
    try:
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        # Default to today
        end_date = timezone.now().date()
    
    attendance_records = attendance_records.filter(
        date__gte=start_date,
        date__lte=end_date
    )
    
    # Calculate attendance statistics
    total_classes = attendance_records.count()
    present_count = attendance_records.filter(status='present').count()
    late_count = attendance_records.filter(status='late').count()
    absent_count = total_classes - present_count - late_count
    
    attendance_rate = 0
    if total_classes > 0:
        attendance_rate = (present_count + late_count) / total_classes * 100
    
    # Attendance by status
    status_data = [
        {
            'status': 'Present',
            'count': present_count
        },
        {
            'status': 'Late',
            'count': late_count
        },
        {
            'status': 'Absent',
            'count': absent_count
        }
    ]
    
    # Attendance by course
    course_data = []
    for course in student.courses.all():
        course_records = attendance_records.filter(class_schedule__course=course)
        course_total = course_records.count()
        if course_total > 0:
            course_present = course_records.filter(status='present').count()
            course_late = course_records.filter(status='late').count()
            course_rate = (course_present + course_late) / course_total * 100
            course_data.append({
                'course': course.code,
                'rate': course_rate
            })
    
    # Attendance by month
    month_data = []
    current_date = timezone.now().date()
    for i in range(6):  # Last 6 months
        month_start = datetime.date(current_date.year, current_date.month, 1) - datetime.timedelta(days=30*i)
        month_end = (month_start.replace(day=28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)
        
        month_records = attendance_records.filter(date__gte=month_start, date__lte=month_end)
        month_total = month_records.count()
        month_present = month_records.filter(status='present').count()
        month_late = month_records.filter(status='late').count()
        
        month_rate = 0
        if month_total > 0:
            month_rate = (month_present + month_late) / month_total * 100
        
        month_data.append({
            'month': month_start.strftime('%b %Y'),
            'rate': month_rate
        })
    
    context = {
        'student': student,
        'attendance_records': attendance_records,
        'total_classes': total_classes,
        'present_count': present_count,
        'late_count': late_count,
        'absent_count': absent_count,
        'attendance_rate': attendance_rate,
        'status_data': json.dumps(status_data),
        'course_data': json.dumps(course_data),
        'month_data': json.dumps(month_data),
        'start_date': start_date,
        'end_date': end_date,
        'courses': student.courses.all(),
        'selected_course': course_id,
    }
    
    return render(request, 'dashboard/student_report.html', context)