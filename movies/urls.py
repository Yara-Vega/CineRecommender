from django.urls import path
from .views import (
    quiz_view,
    home,
    recommend_by_movie,
)

urlpatterns = [
    path('', home, name='home'),  # Page d'accueil
    path('quiz/', quiz_view, name='recommend_by_quiz'),
    path('recommend_movie/', recommend_by_movie, name='recommend_by_movie'),
]
