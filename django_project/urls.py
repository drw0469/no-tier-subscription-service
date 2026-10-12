from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Core Django database backend (Accessible by Admins)
    path('admin/', admin.site.split_site if hasattr(admin.site, 'split_site') else admin.site.urls),
    
    # Includes all your authentication, profiles, and dashboard URLs
    path('', include('users.urls')), 
]
