from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from authentication.models import Department, Course, Student
from core.models import Attendance, ClassSchedule

# @login_required
def get_courses_by_department(request, department_id):
    """Get all courses for a specific department"""
    courses = Course.objects.filter(department_id=department_id).values('id', 'name', 'code')
    return JsonResponse(list(courses), safe=False)

@login_required
def get_attendance_details(request, attendance_id):
    """Get details for a specific attendance record"""
    attendance = get_object_or_404(Attendance, id=attendance_id)
    
    # Check permissions
    if request.user.user_type == 'staff':
        if attendance.class_schedule.instructor.user != request.user:
            return JsonResponse({'error': 'You do not have permission to view this attendance record'}, status=403)
    elif request.user.user_type == 'student':
        if attendance.student.user != request.user:
            return JsonResponse({'error': 'You do not have permission to view this attendance record'}, status=403)
    
    data = {
        'id': attendance.id,
        'student_id': attendance.student.id,
        'student_name': f"{attendance.student.user.first_name} {attendance.student.user.last_name}",
        'class_schedule_id': attendance.class_schedule.id,
        'date': attendance.date.strftime('%Y-%m-%d'),
        'time_in': attendance.time_in.strftime('%H:%M'),
        'status': attendance.status,
        'face_confidence': attendance.face_confidence
    }
    
    return JsonResponse(data)

@login_required
@csrf_exempt
def delete_attendance(request, attendance_id):
    """Delete a specific attendance record"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if request.user.user_type != 'staff':
        return JsonResponse({'error': 'Only staff can delete attendance records'}, status=403)
    
    attendance = get_object_or_404(Attendance, id=attendance_id)
    
    # Check if staff is the instructor for this class
    if attendance.class_schedule.instructor.user != request.user:
        return JsonResponse({'error': 'You do not have permission to delete this attendance record'}, status=403)
    
    try:
        attendance.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@csrf_exempt
def create_attendance(request):
    """Create a new attendance record"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if request.user.user_type != 'staff':
        return JsonResponse({'error': 'Only staff can create attendance records'}, status=403)
    
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        class_schedule_id = data.get('class_schedule_id')
        date = data.get('date')
        status = data.get('status', 'present')
        
        student = get_object_or_404(Student, id=student_id)
        class_schedule = get_object_or_404(ClassSchedule, id=class_schedule_id)
        
        # Check if staff is the instructor for this class
        if class_schedule.instructor.user != request.user:
            return JsonResponse({'error': 'You do not have permission to create attendance for this class'}, status=403)
        
        # Create attendance record
        attendance, created = Attendance.objects.update_or_create(
            student=student,
            class_schedule=class_schedule,
            date=date,
            defaults={
                'time_in': timezone.now().time(),
                'status': status,
                'marked_by': request.user
            }
        )
        
        return JsonResponse({'success': True, 'created': created})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})