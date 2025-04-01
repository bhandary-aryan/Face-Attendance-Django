from django.db import models
from authentication.models import Course, Student, Staff, User

class Session(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    
    def __str__(self):
        return self.name

class ClassSchedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    instructor = models.ForeignKey(Staff, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=(
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ))
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.course.code} - {self.get_day_of_week_display()} {self.start_time} to {self.end_time}"

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    class_schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE)
    date = models.DateField()
    time_in = models.TimeField()
    status = models.CharField(max_length=20, choices=(
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ))
    face_confidence = models.FloatField(default=0.0)  # Confidence score from face recognition
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ('student', 'class_schedule', 'date')
    
    def __str__(self):
        return f"{self.student.student_id} - {self.class_schedule.course.code} - {self.date}"