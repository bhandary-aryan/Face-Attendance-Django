from django.urls import path
from . import views

urlpatterns = [
    path('take-attendance/', views.take_attendance, name='take_attendance'),
    path('take-attendance/<int:class_schedule_id>/', views.take_attendance, name='take_attendance_class'),
    path('train-face/', views.train_face, name='train_face'),

    path('class/<int:class_schedule_id>/recognized-students/', views.get_recognized_students, name='get_recognized_students'),
    path('class/<int:class_schedule_id>/stop-recognition/', views.stop_recognition, name='stop_recognition'),
    path('class/<int:class_schedule_id>/capture-and-recognize/', views.capture_and_recognize, name='capture_and_recognize'),

    path('student/<int:student_id>/qr/', views.generate_student_qr, name='student_qr'),

    # path('attendance/scan/', views.scan_qr_view, name='scan_qr_view'),


]