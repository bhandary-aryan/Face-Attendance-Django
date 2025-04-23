from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin_site.urls),
    # ... existing URL patterns ...
] 