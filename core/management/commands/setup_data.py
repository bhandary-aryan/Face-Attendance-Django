from django.core.management.base import BaseCommand
from authentication.models import Department, Course, User, Student, Staff
from django.db import transaction

class Command(BaseCommand):
    help = 'Sets up initial data for the Face Attendance System'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up initial data...')
        
        # Create departments
        departments = [
            {'name': 'B.Sc.IT Core', 'code': 'BSCIT'},
            {'name': 'B.Sc.IT Cloud Computing', 'code': 'BSCITCC'},
            {'name': 'B.Sc.IT A.I.', 'code': 'BSCITAI'},
            {'name': 'BBA', 'code': 'BBA'},
            {'name': 'M.Sc.IT', 'code': 'MSCIT'},
            {'name': 'MBA', 'code': 'MBA'},
        ]
        
        created_departments = []
        for dept_data in departments:
            dept, created = Department.objects.update_or_create(
                code=dept_data['code'],
                defaults={'name': dept_data['name']}
            )
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f'{status}: Department {dept.name}')
            created_departments.append(dept)
        
        # Create courses for each department
        courses_by_dept = {
            'BSCIT': [
                {'name': 'Introduction to Programming', 'code': 'CS101'},
                {'name': 'Web Development', 'code': 'CS102'},
                {'name': 'Database Systems', 'code': 'CS103'},
            ],
            'BSCITCC': [
                {'name': 'Cloud Computing Basics', 'code': 'CC101'},
                {'name': 'AWS Services', 'code': 'CC102'},
                {'name': 'Cloud Security', 'code': 'CC103'},
            ],
            'BSCITAI': [
                {'name': 'Machine Learning', 'code': 'AI101'},
                {'name': 'Neural Networks', 'code': 'AI102'},
                {'name': 'Computer Vision', 'code': 'AI103'},
            ],
            'BBA': [
                {'name': 'Business Management', 'code': 'BBA101'},
                {'name': 'Marketing', 'code': 'BBA102'},
                {'name': 'Finance', 'code': 'BBA103'},
            ],
            'MSCIT': [
                {'name': 'Advanced Database', 'code': 'MSC101'},
                {'name': 'Advanced Networking', 'code': 'MSC102'},
                {'name': 'Project Management', 'code': 'MSC103'},
            ],
            'MBA': [
                {'name': 'Strategic Management', 'code': 'MBA101'},
                {'name': 'Leadership', 'code': 'MBA102'},
                {'name': 'Operations Management', 'code': 'MBA103'},
            ],
        }
        
        course_count = 0
        for dept_code, courses in courses_by_dept.items():
            try:
                department = Department.objects.get(code=dept_code)
                for course_data in courses:
                    course, created = Course.objects.update_or_create(
                        code=course_data['code'],
                        defaults={
                            'name': course_data['name'],
                            'department': department
                        }
                    )
                    status = 'Created' if created else 'Already exists'
                    self.stdout.write(f'{status}: Course {course.code} - {course.name}')
                    course_count += 1
            except Department.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Department with code {dept_code} does not exist'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully set up {len(created_departments)} departments and {course_count} courses!'))
