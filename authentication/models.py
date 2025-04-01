from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Administrator'),
        ('staff', 'Staff/Teacher'),
        ('student', 'Student'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    face_encodings = models.TextField(null=True, blank=True)  # Store face encoding data as JSON
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    
    # Add related_name attributes to resolve the clash
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='authentication_user_set',  # Custom related_name
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='authentication_user_set',  # Custom related_name
        related_query_name='user',
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return self.name

class Course(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course, related_name='students')
    
    def __str__(self):
        return f"{self.student_id} - {self.user.get_full_name()}"

class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course, related_name='staff')
    
    def __str__(self):
        return f"{self.staff_id} - {self.user.get_full_name()}"