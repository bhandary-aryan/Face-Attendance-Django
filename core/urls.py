from django.urls import path
from . import views

urlpatterns = [
    # Dashboard URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    
    # Attendance URLs
    path('class/<int:class_schedule_id>/attendance/', views.view_attendance, name='view_attendance'),
    path('class/<int:class_schedule_id>/mark-attendance/', views.mark_attendance_manually, name='mark_attendance_manually'),
    path('class/<int:class_schedule_id>/export-attendance/', views.export_attendance, name='export_attendance'),

    # Class Schedule Management URLs
    path('class-schedule/create/', views.create_class_schedule, name='create_class_schedule'),
    path('class-schedules/', views.view_schedules, name='view_schedules'),
    path('class-schedule/<int:schedule_id>/edit/', views.edit_class_schedule, name='edit_class_schedule'),
    path('class-schedule/<int:schedule_id>/delete/', views.delete_class_schedule, name='delete_class_schedule'),

    path('staff/', views.assign_courses, name='view_staff'),
    path('staff/<int:staff_id>/assign-courses/', views.assign_courses, name='assign_courses'),
]