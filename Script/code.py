import pandas
import matplotlib
from dotenv import load_dotenv
import os
import asyncio


load_dotenv(override = True)
print(os.environ["API_tmdb"])
print(os.environ["API_tmdb_lecture"])

from tmdbv3api import TMDb

tmdb = TMDb()
tmdb.api_key = os.environ["API_tmdb"]
tmdb.language = 'en'
tmdb.debug = True

from tmdbv3api import Movie

movie = Movie()
recommendations = movie.recommendations(movie_id=67)

for recommendation in recommendations:
    print(recommendation.title)
    print(recommendation.overview)
    print()

