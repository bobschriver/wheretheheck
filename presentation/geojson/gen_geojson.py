import sqlite3
import numpy
import scipy
import matplotlib.pyplot
import math
import json

from json import dumps
from math import log
from matplotlib.pyplot import get_cmap
from numpy import ones,zeros,convolve,median,dstack,sqrt,sign
from scipy.misc import imsave,imread,imresize
from scipy.ndimage.filters import *

data_directory = "../../data/"

def fetch_transit_frequency(boundaries, sig_digits):
    conn = sqlite3.connect(db_directory + 'busses.db')
    cursor = conn.cursor()

    return cursor.execute("select latitude,longitude,trips_count from stops")

def fetch_neighborhood_destination_transit(boundaries, sig_digits, neighborhoods):
    conn = sqlite3.connect('../data/busses.db')
    cursor = conn.cursor()

    placeholders = ', '.join('?' * len(neighborhoods))

    query = "SELECT latitude,longitude,64 FROM stops WHERE stop_id IN (SELECT stop_id FROM route_stop WHERE route_id IN (SELECT route_id FROM neighborhood_route WHERE neighborhood_id IN (SELECT neighborhood_id FROM neighborhoods WHERE neighborhood_name IN ({0}))))".format(placeholders)

    return cursor.execute(query, neighborhoods)

def fetch_business_quality_for_category(boundaries, sig_digits, category):
    conn = sqlite3.connect('../data/yelp.db')
    cursor = conn.cursor()

    query = "SELECT latitude,longitude,rating FROM businesses WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND num_ratings > 25 AND yelp_id IN (SELECT yelp_id FROM business_category WHERE category_id = (SELECT category_id FROM categories WHERE category_name=?))"

    return cursor.execute(query , [category])


def fetch_business_quality_for_categories(boundaries, sig_digits, categories):
    conn = sqlite3.connect(data_directory + 'yelp.db')
    cursor = conn.cursor()

    placeholders = ', '.join('?' * len(categories))

    query = ("""SELECT b.latitude latitude,b.longitude longitude,c.category_name category,b.rating weight
            FROM businesses b, business_category bc, categories c 
            WHERE b.latitude IS NOT NULL 
            AND b.longitude IS NOT NULL 
            AND b.num_ratings > 25 
            AND b.yelp_id = bc.yelp_id
            AND bc.category_id = c.category_id
            AND c.category_name IN ({0})""").format(placeholders)

    return cursor.execute(query, categories)

def generate_geojson(row):
    geojson = {}
    
    geojson["type"] = "Feature"
    
    geojson["geometry"] = {}
    geojson["geometry"]["type"] = "Point"
    geojson["geometry"]["coordinates"] = [row[0], row[1]]

    geojson["properties"] = {}
    geojson["properties"]["category"] = row[2]
    geojson["properties"]["weight"] = row[3]

    return geojson


north_bound = 47.73414
south_bound = 47.50000

east_bound = -122.41936
west_bound = -122.25285

boundaries = [north_bound, south_bound, east_bound, west_bound]

sig_digits = 4

#categories = [['markets', 5] , ['grocery' , 5] , ['restaurants' , .5] , ['bars' , 1]]
categories = ['markets', 'grocery' , 'restaurants', 'bars']
bqm = fetch_business_quality_for_categories(boundaries, sig_digits, categories)

for bq in bqm:
    print(dumps(generate_geojson(bq), sort_keys=False, indent=2))
