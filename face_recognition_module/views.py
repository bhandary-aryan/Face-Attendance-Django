from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import process_attendance, train_face_model
from core.models import ClassSchedule, Attendance
from authentication.models import Staff, User, Student
from django.utils import timezone
import datetime
import json

@login_required
def take_attendance(request, class_schedule_id=None):
    if request.user.user_type != 'staff':
        messages.error(request, "Only staff members can take attendance.")
        return redirect('dashboard')
    
    try:
        staff = Staff.objects.get(user=request.user)
    except Staff.DoesNotExist:
        messages.error(request, "Staff profile not found.")
        return redirect('dashboard')
    
    if class_schedule_id:
        # This block must be indented
        try:
            class_schedule = ClassSchedule.objects.get(id=class_schedule_id, instructor=staff)
        except ClassSchedule.DoesNotExist:
            messages.error(request, "Class schedule not found or you don't have permission.")
            return redirect('staff_dashboard')
        
        if request.method == 'POST':
            # Use the original process_attendance function directly
            success, message = process_attendance(class_schedule_id, request.user)
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
            return redirect('view_attendance', class_schedule_id=class_schedule_id)
        
        return render(request, 'face_recognition/take_attendance.html', {
            'class_schedule': class_schedule,
        })
    else:
        # This is the else block - also must be indented properly
        # Show list of classes for this staff, filtered by current day of week
        current_day = timezone.now().weekday()  # 0 = Monday, 6 = Sunday
        
        # And so on...
        
        # Filter classes by current day
        today_classes = ClassSchedule.objects.filter(
            instructor=staff,
            day_of_week=current_day
        )
        
        # Get all classes for reference
        all_classes = ClassSchedule.objects.filter(instructor=staff)
        
        day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][current_day]
        
        return render(request, 'face_recognition/class_list.html', {
            'class_schedules': today_classes,
            'all_classes': all_classes,
            'current_day': current_day,
            'day_name': day_name,
            'show_today_only': True
        })

@login_required
def train_face(request):
    if request.method == 'POST':
        success, message = train_face_model(request.user.id)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
    
    return render(request, 'face_recognition/train_face.html')

# New endpoints for real-time face recognition

@login_required
def get_recognized_students(request, class_schedule_id):
    """Get the list of recognized students for a class session"""
    if request.user.user_type != 'staff':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        staff = Staff.objects.get(user=request.user)
        class_schedule = ClassSchedule.objects.get(id=class_schedule_id, instructor=staff)
    except (Staff.DoesNotExist, ClassSchedule.DoesNotExist):
        return JsonResponse({'error': 'Invalid class schedule'}, status=404)
    
    # Get students recognized in this session
    # This uses attendance records created during the ongoing recognition session
    today = timezone.now().date()
    attendance_records = Attendance.objects.filter(
        class_schedule=class_schedule,
        date=today,
        marked_by=request.user
    ).select_related('student', 'student__user')
    
    recognized_students = []
    for record in attendance_records:
        recognized_students.append({
            'id': record.student.id,
            'name': f"{record.student.user.first_name} {record.student.user.last_name}",
            'confidence': record.face_confidence
        })
    
    return JsonResponse({'recognized_students': recognized_students})

@login_required
@csrf_exempt
def stop_recognition(request, class_schedule_id):
    """Stop the face recognition process for a class"""
    if request.method != 'POST' or request.user.user_type != 'staff':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        staff = Staff.objects.get(user=request.user)
        class_schedule = ClassSchedule.objects.get(id=class_schedule_id, instructor=staff)
    except (Staff.DoesNotExist, ClassSchedule.DoesNotExist):
        return JsonResponse({'error': 'Invalid class schedule'}, status=404)
    
    # Here you would implement any logic to stop ongoing recognition processes
    # For example, setting a flag in the session or database
    # This is a placeholder that simply returns success
    
    return JsonResponse({'success': True})

@login_required
@csrf_exempt
def capture_and_recognize(request, class_schedule_id):
    """Process a single frame for face recognition"""
    if request.method != 'POST' or request.user.user_type != 'staff':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        staff = Staff.objects.get(user=request.user)
        class_schedule = ClassSchedule.objects.get(id=class_schedule_id, instructor=staff)
    except (Staff.DoesNotExist, ClassSchedule.DoesNotExist):
        return JsonResponse({'error': 'Invalid class schedule'}, status=404)
    
    try:
        # Get the image data from the request
        data = json.loads(request.body)
        image_data = data.get('image_data')
        
        if not image_data:
            return JsonResponse({'error': 'No image data provided'}, status=400)
        
        # Process the image data (this is a placeholder)
        # In a real implementation, you would:
        # 1. Decode the base64 image
        # 2. Run face recognition on it
        # 3. Update attendance records for recognized students
        # 4. Return the list of recognized students
        
        # For now, this returns an empty list as we're using the existing
        # process_attendance function for actual recognition
        return JsonResponse({'recognized_students': []})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)