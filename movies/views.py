from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import requests
import re
import os
from dotenv import load_dotenv

# Charger les variables d’environnement
load_dotenv()
OMDB_API_KEY = os.getenv("OMDB_API_KEY")  # Clé API récupérée depuis .env

# Chargement des données
movies = pd.read_csv("movies.csv")
ratings = pd.read_csv("ratings.csv")

# Calcul des notes moyennes
average_ratings = ratings.groupby('movieId')['rating'].mean().reset_index()
average_ratings.columns = ['movieId', 'avg_rating']
movies = pd.merge(movies, average_ratings, on='movieId', how='left')

# Extraction de l'année depuis le titre
def extract_year(title):
    match = re.search(r'\((\d{4})\)', title)
    return int(match.group(1)) if match else None

movies['year'] = movies['title'].apply(extract_year)

# Appel à l’API OMDb pour récupérer l’URL de l’affiche
def get_poster_url(title):
    clean_title = re.sub(r'\s*\(\d{4}\)', '', title)
    url = f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={clean_title}'
    try:
        response = requests.get(url)
        data = response.json()
        if data.get('Response') == 'True' and data.get('Poster') != 'N/A':
            return data['Poster']
    except Exception as e:
        print(f"Erreur API OMDb: {e}")
    return ''  # Retourner une chaîne vide si l'image n'est pas disponible

# Page d’accueil
def home(request):
    return render(request, 'movies/home.html')

# Recommandation par film avec filtrage ±5 ans
def recommend_by_movie(request):
    selected_title = request.GET.get('movie_title')

    if not selected_title:
        return render(request, 'movies/recommend_by_movie.html', {'movies': movies['title'].tolist()})

    movies['genres'] = movies['genres'].fillna('')
    vectorizer = CountVectorizer(tokenizer=lambda x: x.split('|'))
    genre_matrix = vectorizer.fit_transform(movies['genres'])
    similarity = cosine_similarity(genre_matrix)

    try:
        idx = movies[movies['title'] == selected_title].index[0]
    except IndexError:
        return HttpResponse("Film non trouvé.")

    selected_year = movies.iloc[idx]['year']
    sim_scores = list(enumerate(similarity[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    recommended = []
    for i, score in sim_scores:
        if i == idx:
            continue
        movie = movies.iloc[i]
        if selected_year and movie['year'] and abs(movie['year'] - selected_year) <= 5:
            recommended.append(movie)
        if len(recommended) == 10:
            break

    recommended_movies = []
    for movie in recommended:
        movie_dict = movie.to_dict()
        movie_dict['poster_url'] = get_poster_url(movie['title'])  # Récupérer l'URL de l'affiche
        recommended_movies.append(movie_dict)

    return render(request, 'movies/recommended_movies.html', {
        'recommended_movies': recommended_movies,
        'selected_title': selected_title
    })

# Quiz
@csrf_exempt
def quiz_view(request):
    if request.method == 'POST':
        genre = request.POST.get('genre')
        period = request.POST.get('period')
        popularity = request.POST.get('popularity')

        filtered_movies = movies[movies['genres'].str.contains(genre, na=False)]

        if period == 'recent':
            filtered_movies = filtered_movies[filtered_movies['year'] >= 2015]
        else:
            filtered_movies = filtered_movies[filtered_movies['year'] < 2015]

        recommended_movies = filtered_movies.head(10).to_dict(orient='records')
        for movie in recommended_movies:
            movie['poster_url'] = get_poster_url(movie['title'])  # Récupérer l'URL de l'affiche

        return render(request, 'movies/recommended_movies.html', {
            'recommended_movies': recommended_movies
        })

    return render(request, 'movies/quiz.html')
