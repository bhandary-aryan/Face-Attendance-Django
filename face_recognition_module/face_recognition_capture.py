# import cv2
# from pyzbar.pyzbar import decode
# from django.core.signing import Signer, BadSignature
# import django
# import os
# from datetime import datetime
# from face_recognition_module.models import Student, Attendance

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FaceAttendance.settings')
# django.setup()

# cap = cv2.VideoCapture(0)
# signer = Signer()

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     decoded_objects = decode(frame)
#     for obj in decoded_objects:
#         qr_token = obj.data.decode('utf-8')

#         try:
#             student_id = signer.unsign(qr_token)
#             student = Student.objects.get(uuid=student_id)

#             # Mark attendance if not already marked
#             if not Attendance.objects.filter(student=student, date=datetime.today().date()).exists():
#                 Attendance.objects.create(student=student)
#                 print(f"{student.name} marked present via QR.")

#             cv2.putText(frame, f"{student.name} Present", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

#         except (BadSignature, Student.DoesNotExist):
#             cv2.putText(frame, "Invalid QR", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

#     # Show the frame
#     cv2.imshow("QR Attendance", frame)

#     # Press 'q' to exit
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()
