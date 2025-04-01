from django.urls import path
from . import views

urlpatterns = [
    path('department/<int:department_id>/courses/', views.get_courses_by_department, name='get_courses_by_department'),
    path('attendance/<int:attendance_id>/', views.get_attendance_details, name='get_attendance_details'),
    path('attendance/<int:attendance_id>/delete/', views.delete_attendance, name='delete_attendance'),
    path('attendance/create/', views.create_attendance, name='create_attendance'),
]