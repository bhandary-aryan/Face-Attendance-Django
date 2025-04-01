from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
import face_recognition
import json
import numpy as np
from .forms import UserLoginForm, StudentRegistrationForm, StaffRegistrationForm, UserProfileForm
from face_recognition_module.utils import train_face_model
from .forms import UserLoginForm, StudentRegistrationForm, StaffRegistrationForm
from .models import User, Student, Staff, Department

@csrf_protect
def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome, {user.get_full_name()}!")
            
            if user.user_type == 'admin':
                return redirect('admin_dashboard')
            elif user.user_type == 'staff':
                return redirect('staff_dashboard')
            else:
                return redirect('student_dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()
    
    return render(request, 'authentication/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@csrf_protect
def register_student_view(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create user
            user = form.save(commit=False)
            user.user_type = 'student'
            user.address = form.cleaned_data['address']
            user.phone_number = form.cleaned_data['phone_number']
            user.save()
            
            # Process face encoding
            profile_pic = request.FILES['profile_pic']
            image = face_recognition.load_image_file(profile_pic)
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                user.delete()
                messages.error(request, "No face detected in the uploaded image. Please try again.")
                return redirect('register_student')
            
            face_encoding = face_recognition.face_encodings(image, face_locations)[0]
            user.face_encodings = json.dumps(face_encoding.tolist())
            user.save()
            
            # Create student profile
            student = Student.objects.create(
                user=user,
                student_id=form.cleaned_data['student_id'],
                department=Department.objects.get(id=request.POST.get('department'))
            )
            
            # Add courses
            courses = request.POST.getlist('courses')
            for course_id in courses:
                student.courses.add(course_id)
            
            messages.success(request, f"Account created for {user.username}!")
            return redirect('login')
    else:
        form = StudentRegistrationForm()
    
    departments = Department.objects.all()
    return render(request, 'authentication/register_student.html', {
        'form': form,
        'departments': departments,
    })

@csrf_protect
def register_staff_view(request):
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create user
            user = form.save(commit=False)
            user.user_type = 'staff'
            user.address = form.cleaned_data['address']
            user.phone_number = form.cleaned_data['phone_number']
            user.save()
            
            # Create staff profile
            staff = Staff.objects.create(
                user=user,
                staff_id=form.cleaned_data['staff_id'],
                department=Department.objects.get(id=request.POST.get('department'))
            )
            
            # Add courses
            courses = request.POST.getlist('courses')
            for course_id in courses:
                staff.courses.add(course_id)
            
            messages.success(request, f"Account created for {user.username}!")
            return redirect('login')
    else:
        form = StaffRegistrationForm()
    
    departments = Department.objects.all()
    return render(request, 'authentication/register_staff.html', {
        'form': form,
        'departments': departments,
    })



@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()
            
            # If profile pic was updated, retrain face model if user is student or staff
            if 'profile_pic' in form.changed_data and user.user_type in ['student', 'staff']:
                success, message = train_face_model(user.id)
                if success:
                    messages.success(request, "Profile updated and face model retrained successfully.")
                else:
                    messages.warning(request, f"Profile updated but face model training failed: {message}")
            else:
                messages.success(request, "Profile updated successfully.")
                
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'authentication/profile.html', {
        'form': form
    })