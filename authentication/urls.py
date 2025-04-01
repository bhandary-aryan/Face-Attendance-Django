from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/student/', views.register_student_view, name='register_student'),
    path('register/staff/', views.register_staff_view, name='register_staff'),
    path('profile/', views.profile_view, name='profile'),

]