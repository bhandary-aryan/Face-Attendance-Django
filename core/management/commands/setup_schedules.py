from django.core.management.base import BaseCommand
from authentication.models import Department, Course, Staff
from core.models import ClassSchedule, Session
from django.db import transaction
import datetime

class Command(BaseCommand):
    help = 'Sets up class schedules from Sunday to Friday for the Face Attendance System'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up class schedules from Sunday to Friday...')
        
        # Get or create a session
        session, _ = Session.objects.get_or_create(
            name='Spring 2025',
            defaults={
                'start_date': datetime.date(2025, 1, 15),
                'end_date': datetime.date(2025, 5, 15)
            }
        )
        
        # Define day mapping (0=Monday, 6=Sunday in Django)
        # But we'll use 6=Sunday, 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday
        # Skip Saturday (5)
        day_names = {
            6: 'Sunday',
            0: 'Monday',
            1: 'Tuesday',
            2: 'Wednesday',
            3: 'Thursday',
            4: 'Friday'
        }
        
        # Try to get existing courses and staff
        try:
            courses = list(Course.objects.all())
            staff_members = list(Staff.objects.all())
            
            if not courses:
                self.stdout.write(self.style.ERROR("No courses found. Please run 'setup_data' command first."))
                return
                
            if not staff_members:
                self.stdout.write(self.style.ERROR("No staff members found. Please create staff accounts first."))
                return
                
            # For demonstration, use the first staff member
            staff = staff_members[0]
            
            created_count = 0
            
            # Create time slots
            time_slots = [
                ('08:00', '09:30'),
                ('10:00', '11:30'),
                ('12:00', '13:30'),
                ('14:00', '15:30'),
                ('16:00', '17:30')
            ]
            
            # Create schedules for each day (Sunday to Friday)
            course_index = 0
            for day in [6, 0, 1, 2, 3, 4]:  # Sunday to Friday
                day_name = day_names[day]
                self.stdout.write(f"Creating schedules for {day_name}...")
                
                # Create 2-3 classes per day
                num_classes = min(len(time_slots), len(courses) - course_index)
                
                for i in range(num_classes):
                    course = courses[course_index % len(courses)]
                    course_index += 1
                    
                    start_time, end_time = time_slots[i]
                    
                    # Parse times
                    start_time_obj = datetime.datetime.strptime(start_time, '%H:%M').time()
                    end_time_obj = datetime.datetime.strptime(end_time, '%H:%M').time()
                    
                    # Create room number (floor based on day, room number based on time slot)
                    room = f"{day+1}{i+1}"
                    
                    # Create or update class schedule
                    schedule, created = ClassSchedule.objects.update_or_create(
                        course=course,
                        instructor=staff,
                        day_of_week=day,
                        start_time=start_time_obj,
                        end_time=end_time_obj,
                        defaults={
                            'room': room,
                            'session': session
                        }
                    )
                    
                    status = 'Created' if created else 'Updated'
                    self.stdout.write(f"  {status}: {course.code} on {day_name} at {start_time}-{end_time} in Room {room}")
                    created_count += int(created)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} class schedules!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating schedules: {str(e)}"))