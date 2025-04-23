from django.urls import path, include
from attendance.admin import admin_site

# Register the admin site
admin_site.final_catch_all_view = False

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', include('attendance.urls')),
] 