import pandas
import matplotlib
from dotenv import load_dotenv
import os
import asyncio
import pandas as pd

from datetime import datetime, timedelta
import gzip
import io
import requests




### TESTS DES SECRETS

load_dotenv(override = True)
print(os.environ["API_tmdb"])
print(os.environ["API_tmdb_lecture"])




### CONFIGURATIONS

from tmdbv3api import TMDb

tmdb = TMDb()
tmdb.api_key = os.environ["API_tmdb"]
tmdb.language = 'fr'
tmdb.debug = True




### TESTS (print des recommendations)

from tmdbv3api import Movie

movie_api = Movie()
recommendations = movie_api.recommendations(movie_id=67)

#for recommendation in recommendations:
#    print(recommendation.title)
#    print(recommendation.overview)
#    print()




### MISE EN FORME DES DONNÉES (en pandas)



