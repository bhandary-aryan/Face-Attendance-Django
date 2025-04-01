from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
import datetime
import csv
import xlwt

from .models import ClassSchedule, Attendance, Session
from authentication.models import Student, Staff, Course, Department, User

# Dashboard views
@login_required
def admin_dashboard(request):
    if request.user.user_type != 'admin':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    total_students = Student.objects.count()
    total_staff = Staff.objects.count()
    total_courses = Course.objects.count()
    total_departments = Department.objects.count()
    
    recent_attendance = Attendance.objects.select_related('student', 'class_schedule').order_by('-date', '-time_in')[:10]
    
    attendance_stats = Attendance.objects.values('status').annotate(count=Count('id'))
    
    context = {
        'total_students': total_students,
        'total_staff': total_staff,
        'total_courses': total_courses,
        'total_departments': total_departments,
        'recent_attendance': recent_attendance,
        'attendance_stats': attendance_stats,
    }
    
    return render(request, 'core/admin_dashboard.html', context)

@login_required
def staff_dashboard(request):
    if request.user.user_type != 'staff':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    try:
        staff = Staff.objects.get(user=request.user)
    except Staff.DoesNotExist:
        messages.error(request, "Staff profile not found.")
        return redirect('dashboard')
    
    # Get courses taught by this staff
    courses = staff.courses.all()
    
    # Get class schedules for this staff
    class_schedules = ClassSchedule.objects.filter(instructor=staff)
    
    # Get today's classes
    today = timezone.now().date()
    day_of_week = today.weekday()
    today_classes = class_schedules.filter(day_of_week=day_of_week)
    
    # Get recent attendance records
    recent_attendance = Attendance.objects.filter(
        class_schedule__instructor=staff
    ).select_related('student', 'class_schedule').order_by('-date', '-time_in')[:10]
    
    context = {
        'staff': staff,
        'courses': courses,
        'class_schedules': class_schedules,
        'today_classes': today_classes,
        'recent_attendance': recent_attendance,
    }
    
    return render(request, 'core/staff_dashboard.html', context)

@login_required
def student_dashboard(request):
    if request.user.user_type != 'student':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('dashboard')
    
    # Get courses enrolled by this student
    courses = student.courses.all()
    
    # Get today's classes
    today = timezone.now().date()
    day_of_week = today.weekday()
    today_classes = ClassSchedule.objects.filter(
        course__in=courses,
        day_of_week=day_of_week
    )
    
    # Get recent attendance records
    attendance_records = Attendance.objects.filter(
        student=student
    ).select_related('class_schedule').order_by('-date')
    
    # Calculate attendance statistics
    total_classes = attendance_records.count()
    present_count = attendance_records.filter(status='present').count()
    late_count = attendance_records.filter(status='late').count()
    absent_count = attendance_records.filter(status='absent').count()
    
    attendance_rate = 0
    if total_classes > 0:
        attendance_rate = (present_count + late_count) / total_classes * 100
    
    context = {
        'student': student,
        'courses': courses,
        'today_classes': today_classes,
        'attendance_records': attendance_records[:10],
        'total_classes': total_classes,
        'present_count': present_count,
        'late_count': late_count,
        'absent_count': absent_count,
        'attendance_rate': attendance_rate,
    }
    
    return render(request, 'core/student_dashboard.html', context)

# Attendance views
@login_required
def view_attendance(request, class_schedule_id):
    class_schedule = get_object_or_404(ClassSchedule, id=class_schedule_id)
    
    # Check permissions
    if request.user.user_type == 'staff':
        try:
            staff = Staff.objects.get(user=request.user)
            if class_schedule.instructor != staff:
                messages.error(request, "You don't have permission to view this attendance.")
                return redirect('staff_dashboard')
        except Staff.DoesNotExist:
            messages.error(request, "Staff profile not found.")
            return redirect('dashboard')
    elif request.user.user_type == 'student':
        try:
            student = Student.objects.get(user=request.user)
            if class_schedule.course not in student.courses.all():
                messages.error(request, "You are not enrolled in this class.")
                return redirect('student_dashboard')
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found.")
            return redirect('dashboard')
    
    # Get date from request or use today
    date_str = request.GET.get('date')
    if date_str:
        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            date = timezone.now().date()
    else:
        date = timezone.now().date()
    
    # Get attendance records
    attendance_records = Attendance.objects.filter(
        class_schedule=class_schedule,
        date=date
    ).select_related('student', 'student__user')
    
    # Get all students enrolled in this course
    enrolled_students = Student.objects.filter(courses=class_schedule.course)
    
    # Find missing students (absent)
    present_student_ids = [record.student.id for record in attendance_records]
    absent_students = enrolled_students.exclude(id__in=present_student_ids)
    
    context = {
        'class_schedule': class_schedule,
        'date': date,
        'attendance_records': attendance_records,
        'absent_students': absent_students,
    }
    
    return render(request, 'core/view_attendance.html', context)

@login_required
def mark_attendance_manually(request, class_schedule_id):
    if request.user.user_type != 'staff':
        messages.error(request, "Only staff members can mark attendance.")
        return redirect('dashboard')
    
    class_schedule = get_object_or_404(ClassSchedule, id=class_schedule_id)
    
    try:
        staff = Staff.objects.get(user=request.user)
        if class_schedule.instructor != staff:
            messages.error(request, "You don't have permission to mark attendance for this class.")
            return redirect('staff_dashboard')
    except Staff.DoesNotExist:
        messages.error(request, "Staff profile not found.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        date_str = request.POST.get('date')
        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            date = timezone.now().date()
        
        student_ids = request.POST.getlist('student_id')
        statuses = request.POST.getlist('status')
        
        for i, student_id in enumerate(student_ids):
            student = get_object_or_404(Student, id=student_id)
            status = statuses[i] if i < len(statuses) else 'absent'
            
            if status in ['present', 'late']:
                # Create or update attendance record
                Attendance.objects.update_or_create(
                    student=student,
                    class_schedule=class_schedule,
                    date=date,
                    defaults={
                        'time_in': timezone.now().time(),
                        'status': status,
                        'marked_by': request.user
                    }
                )
            elif status == 'absent':
                # Delete any existing record (if exists)
                Attendance.objects.filter(
                    student=student,
                    class_schedule=class_schedule,
                    date=date
                ).delete()
        
        messages.success(request, "Attendance marked successfully.")
        return redirect('view_attendance', class_schedule_id=class_schedule_id)
    
    # Get all students enrolled in this course
    enrolled_students = Student.objects.filter(
        courses=class_schedule.course
    ).select_related('user')
    
    context = {
        'class_schedule': class_schedule,
        'enrolled_students': enrolled_students,
        'today': timezone.now().date(),
    }
    
    return render(request, 'core/mark_attendance.html', context)
@login_required
def export_attendance(request, class_schedule_id):
    if request.user.user_type not in ['admin', 'staff']:
        messages.error(request, "You don't have permission to export attendance.")
        return redirect('dashboard')
    
    class_schedule = get_object_or_404(ClassSchedule, id=class_schedule_id)
    
    if request.user.user_type == 'staff':
        try:
            staff = Staff.objects.get(user=request.user)
            if class_schedule.instructor != staff:
                messages.error(request, "You don't have permission to export this attendance.")
                return redirect('staff_dashboard')
        except Staff.DoesNotExist:
            messages.error(request, "Staff profile not found.")
            return redirect('dashboard')
    
    # Get date range from request
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
    
    # Get all students enrolled in this course
    enrolled_students = Student.objects.filter(
        courses=class_schedule.course
    ).select_related('user')
    
    # Get date range
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        # Only include days matching the class schedule day of week
        if current_date.weekday() == class_schedule.day_of_week:
            date_range.append(current_date)
        current_date += datetime.timedelta(days=1)
    
    # Format for export
    export_format = request.GET.get('format', 'excel')
    
    if export_format == 'excel':
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{class_schedule.course.code}_attendance_{start_date}_to_{end_date}.xls"'
        
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Attendance')
        
        # Sheet header
        row_num = 0
        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        
        columns = ['Student ID', 'Name']
        for date in date_range:
            columns.append(date.strftime('%Y-%m-%d'))
        
        for col_num, column_title in enumerate(columns):
            ws.write(row_num, col_num, column_title, font_style)
        
        # Sheet data
        font_style = xlwt.XFStyle()
        
        for student in enrolled_students:
            row_num += 1
            ws.write(row_num, 0, student.student_id, font_style)
            ws.write(row_num, 1, f"{student.user.first_name} {student.user.last_name}", font_style)
            
            for col_num, date in enumerate(date_range, 2):
                try:
                    attendance = Attendance.objects.get(
                        student=student,
                        class_schedule=class_schedule,
                        date=date
                    )
                    ws.write(row_num, col_num, attendance.status, font_style)
                except Attendance.DoesNotExist:
                    ws.write(row_num, col_num, 'absent', font_style)
        
        wb.save(response)
        return response
    
    elif export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{class_schedule.course.code}_attendance_{start_date}_to_{end_date}.csv"'
        
        writer = csv.writer(response)
        
        # CSV header
        header = ['Student ID', 'Name']
        for date in date_range:
            header.append(date.strftime('%Y-%m-%d'))
        writer.writerow(header)
        
        # CSV data
        for student in enrolled_students:
            row = [
                student.student_id,
                f"{student.user.first_name} {student.user.last_name}"
            ]
            
            for date in date_range:
                try:
                    attendance = Attendance.objects.get(
                        student=student,
                        class_schedule=class_schedule,
                        date=date
                    )
                    row.append(attendance.status)
                except Attendance.DoesNotExist:
                    row.append('absent')
            
            writer.writerow(row)
        
        return response
    
    # Default: show attendance report page
    context = {
        'class_schedule': class_schedule,
        'enrolled_students': enrolled_students,
        'date_range': date_range,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'core/export_attendance.html', context)

# Class Schedule Management Views
@login_required
def create_class_schedule(request):
    if request.user.user_type != 'admin':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Process form data
        course_id = request.POST.get('course')
        staff_id = request.POST.get('staff')
        day_of_week = request.POST.get('day_of_week')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        room = request.POST.get('room')
        session_id = request.POST.get('session')
        
        try:
            course = Course.objects.get(id=course_id)
            staff = Staff.objects.get(id=staff_id)
            session = Session.objects.get(id=session_id)
            
            # Create class schedule
            ClassSchedule.objects.create(
                course=course,
                instructor=staff,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                room=room,
                session=session
            )
            
            messages.success(request, "Class schedule created successfully.")
            return redirect('view_schedules')
        except (Course.DoesNotExist, Staff.DoesNotExist, Session.DoesNotExist) as e:
            messages.error(request, f"Error: {str(e)}")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    
    # Get data for form
    courses = Course.objects.all()
    staff = Staff.objects.all()
    sessions = Session.objects.all()
    
    context = {
        'courses': courses,
        'staff': staff,
        'sessions': sessions,
        'days_of_week': [(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), 
                         (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')]
    }
    
    return render(request, 'core/create_class_schedule.html', context)

@login_required
def view_schedules(request):
    """View all class schedules"""
    if request.user.user_type not in ['admin', 'staff']:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    # Filter options
    department_id = request.GET.get('department')
    course_id = request.GET.get('course')
    staff_id = request.GET.get('staff')
    day = request.GET.get('day')
    
    # Base queryset
    schedules = ClassSchedule.objects.select_related('course', 'instructor', 'session')
    
    # Apply filters
    if department_id:
        schedules = schedules.filter(course__department_id=department_id)
    
    if course_id:
        schedules = schedules.filter(course_id=course_id)
    
    if staff_id:
        schedules = schedules.filter(instructor_id=staff_id)
    
    if day is not None and day != '':
        schedules = schedules.filter(day_of_week=int(day))
    
    # Staff can only see their own schedules
    if request.user.user_type == 'staff':
        try:
            staff = Staff.objects.get(user=request.user)
            schedules = schedules.filter(instructor=staff)
        except Staff.DoesNotExist:
            schedules = ClassSchedule.objects.none()
    
    # Get filter options
    departments = Department.objects.all()
    courses = Course.objects.all()
    staff_members = Staff.objects.select_related('user').all()
    
    context = {
        'schedules': schedules,
        'departments': departments,
        'courses': courses,
        'staff_members': staff_members,
        'days_of_week': [(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), 
                         (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')],
        'selected_department': department_id,
        'selected_course': course_id,
        'selected_staff': staff_id,
        'selected_day': day
    }
    
    return render(request, 'core/view_schedules.html', context)

@login_required
def edit_class_schedule(request, schedule_id):
    """Edit a class schedule"""
    if request.user.user_type != 'admin':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    schedule = get_object_or_404(ClassSchedule, id=schedule_id)
    
    if request.method == 'POST':
        # Process form data
        course_id = request.POST.get('course')
        staff_id = request.POST.get('staff')
        day_of_week = request.POST.get('day_of_week')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        room = request.POST.get('room')
        session_id = request.POST.get('session')
        
        try:
            course = Course.objects.get(id=course_id)
            staff = Staff.objects.get(id=staff_id)
            session = Session.objects.get(id=session_id)
            
            # Update schedule
            schedule.course = course
            schedule.instructor = staff
            schedule.day_of_week = day_of_week
            schedule.start_time = start_time
            schedule.end_time = end_time
            schedule.room = room
            schedule.session = session
            schedule.save()
            
            messages.success(request, "Class schedule updated successfully.")
            return redirect('view_schedules')
        except (Course.DoesNotExist, Staff.DoesNotExist, Session.DoesNotExist) as e:
            messages.error(request, f"Error: {str(e)}")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    
    # Get data for form
    courses = Course.objects.all()
    staff_members = Staff.objects.all()
    sessions = Session.objects.all()
    
    context = {
        'schedule': schedule,
        'courses': courses,
        'staff_members': staff_members,
        'sessions': sessions,
        'days_of_week': [(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), 
                         (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')]
    }
    
    return render(request, 'core/edit_class_schedule.html', context)

@login_required
def delete_class_schedule(request, schedule_id):
    """Delete a class schedule"""
    if request.user.user_type != 'admin':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    schedule = get_object_or_404(ClassSchedule, id=schedule_id)
    
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, "Class schedule deleted successfully.")
        return redirect('view_schedules')
    
    return render(request, 'core/delete_class_schedule.html', {'schedule': schedule})

@login_required
def assign_courses(request, staff_id=None):
    if request.user.user_type != 'admin':
        messages.error(request, "Only administrators can assign courses.")
        return redirect('dashboard')
    
    # If staff_id is provided, we're editing a specific staff member
    # Otherwise, show a list of staff to choose from
    if staff_id:
        staff = get_object_or_404(Staff, id=staff_id)
        
        if request.method == 'POST':
            # Get the list of selected course IDs
            course_ids = request.POST.getlist('courses')
            
            # Clear current courses and add the selected ones
            staff.courses.clear()
            for course_id in course_ids:
                try:
                    course = Course.objects.get(id=course_id)
                    staff.courses.add(course)
                except Course.DoesNotExist:
                    continue
            
            messages.success(request, f"Courses assigned to {staff.user.get_full_name()} successfully.")
            return redirect('view_staff')
        
        # Get all available courses
        all_courses = Course.objects.all()
        # Get the IDs of courses already assigned to this staff
        assigned_course_ids = staff.courses.values_list('id', flat=True)
        
        context = {
            'staff': staff,
            'all_courses': all_courses,
            'assigned_course_ids': list(assigned_course_ids),
        }
        
        return render(request, 'core/assign_courses.html', context)
    else:
        # Show list of staff members
        staff_members = Staff.objects.select_related('user', 'department').all()
        context = {
            'staff_members': staff_members,
        }
        return render(request, 'core/staff_list.html', context)