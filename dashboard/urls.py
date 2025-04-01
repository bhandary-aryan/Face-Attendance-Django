from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_redirect, name='dashboard'),
    path('analytics/', views.attendance_analytics, name='attendance_analytics'),
    path('student-report/', views.student_attendance_report, name='student_report'),
    path('student-report/<int:student_id>/', views.student_attendance_report, name='student_report_specific'),
]