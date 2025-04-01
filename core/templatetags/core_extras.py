from django import template
from django.utils import timezone
from core.models import Attendance

register = template.Library()

@register.filter
def filter_day(class_schedules, day_of_week):
    """Filter class schedules by day of week"""
    return class_schedules.filter(day_of_week=day_of_week)

@register.filter
def get_attendance_status(class_schedule, student):
    """Get the attendance status for a student in a specific class for today"""
    try:
        today = timezone.now().date()
        attendance = Attendance.objects.get(
            student=student,
            class_schedule=class_schedule,
            date=today
        )
        return attendance.status
    except Attendance.DoesNotExist:
        # Check if class hasn't started yet
        current_time = timezone.now().time()
        if current_time < class_schedule.start_time:
            return 'marked'
        return 'absent'

@register.simple_tag
def get_attendance_count(student, course, status=None):
    """Get attendance count for a student in a course with optional status filter"""
    query = {
        'student': student,
        'class_schedule__course': course
    }
    if status:
        query['status'] = status
    
    return Attendance.objects.filter(**query).count()

@register.simple_tag
def get_attendance_rate(student, course):
    """Calculate attendance rate for a student in a course"""
    total = Attendance.objects.filter(
        student=student,
        class_schedule__course=course
    ).count()
    
    if total == 0:
        return 0
    
    present_count = Attendance.objects.filter(
        student=student,
        class_schedule__course=course,
        status__in=['present', 'late']
    ).count()
    
    return (present_count / total) * 100
