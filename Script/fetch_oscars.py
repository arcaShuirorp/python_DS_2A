import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime, timedelta
import gzip
import io
import requests
from tmdbv3api import TMDb, Movie
from fetch_TMDB import fetch_movie_details

