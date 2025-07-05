import cv2
from pyzbar.pyzbar import decode
import django
import os
from datetime import datetime
from django.utils import timezone

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FaceAttendance.settings')
django.setup()

from core.models import Student, Attendance

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    decoded_objects = decode(frame)
    for obj in decoded_objects:
        data = obj.data.decode('utf-8')

        if data.startswith("SID:"):
            student_id = data.replace("SID:", "")
            try:
                student = Student.objects.select_related('user', 'department').get(id=student_id)

                # Mark attendance
                if not Attendance.objects.filter(student=student, date=datetime.today().date()).exists():
                    Attendance.objects.create(
                        student=student,
                        date=timezone.now().date(),
                        time_in=timezone.now().time()
                    )
                    print(f"[✔] Attendance marked for {student.user.get_full_name()}")

                # Display student details
                details = (
                    f"Name: {student.user.get_full_name()} | "
                    f"Student ID: {student.student_id} | "
                    f"Dept: {student.department.name} | "
                    f"Phone: {student.user.phone_number}"
                )
                print(details)

                cv2.putText(frame, details, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            except Student.DoesNotExist:
                cv2.putText(frame, "Invalid Student ID", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("QR Attendance Scanner", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()
