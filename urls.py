from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('movies/', include('movies.urls')),  # Ici, on inclut les URLs de l'application "movies"
]
path('movies/', include('movies.urls')),
