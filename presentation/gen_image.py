import sqlite3
import numpy
import scipy
import matplotlib.pyplot
import matplotlib.cm

from matplotlib.pyplot import hexbin,show
from numpy import ones,zeros,convolve,median,dstack
from scipy.misc import imsave,imread,imresize
from scipy.ndimage.filters import *

def lat_long_to_x_y(boundaries, sig_digits, data_list):
	north_bound = boundaries[0]
	south_bound = boundaries[1]
	east_bound = boundaries[2]
	west_bound = boundaries[3]

	sig_digits_shift = 10 ** sig_digits
	
	height = int((north_bound - south_bound) * sig_digits_shift) 
	width = int(abs(east_bound - west_bound) * sig_digits_shift)

	shifted_data = [[] , [], []]	

	median_value = median([data[2] for data in data_list])
	norm_median = 128
	norm_max = 255

	for data in data_list:
		latitude = data[0]
		longitude = data[1]
		value = data[2]
		norm_value = value * (norm_median / median_value)
		
		if norm_value > norm_max:
			norm_value = norm_max
		
		if north_bound > latitude > south_bound and west_bound > longitude > east_bound: 

			x_index = int(abs(longitude - east_bound) * sig_digits_shift)
			y_index = int((latitude - south_bound) * sig_digits_shift)

			shifted_data[0].append(x_index)
			shifted_data[1].append(y_index)
			shifted_data[2].append(norm_value)
	
	return shifted_data

def generate_general_transit_list(boundaries, sig_digits):
	conn = sqlite3.connect('../data/busses.db')
	cursor = conn.cursor()

	stops = cursor.execute("select latitude,longitude,trips_count from stops").fetchall()

	gtl = lat_long_to_x_y(boundaries, sig_digits, stops)

	return gtl

def generate_neighborhood_destination_transit_matrix(boundaries, sig_digits, neighborhoods):
	conn = sqlite3.connect('../data/busses.db')
	cursor = conn.cursor()

	placeholders = ', '.join('?' * len(neighborhoods))

	query = "SELECT latitude,longitude,255 FROM stops WHERE stop_id IN (SELECT stop_id FROM route_stop WHERE route_id IN (SELECT route_id FROM neighborhood_route WHERE neighborhood_id IN (SELECT neighborhood_id FROM neighborhoods WHERE neighborhood_name IN (%s))))" % placeholders

	stops = cursor.execute(query, neighborhoods)

	ndtm = generate_matrix(boundaries, sig_digits, stops)
	
	return ndtm

def generate_business_quality_list_for_category(boundaries, sig_digits, category, category_weight):
	conn = sqlite3.connect('../data/yelp.db')
	cursor = conn.cursor()

	query = "SELECT latitude, longitude, rating, num_ratings FROM businesses WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND yelp_id IN (SELECT yelp_id FROM business_category WHERE category_id = (SELECT category_id FROM categories WHERE category_name=?))"

	quality_raw = cursor.execute(query , [category]).fetchall()

	quality = [[quality_data[0], quality_data[1], quality_data[2] * quality_data[3]] * category_weight for quality_data in quality_raw]
	
	bql = lat_long_to_x_y(boundaries, sig_digits, quality)

	return bql

def generate_business_quality_list(boundaries, sig_digits, categories):

	bql = [[], [], []]
	for category,category_weight in categories:
		bql_category = generate_business_quality_list_for_category(boundaries, sig_digits, category, category_weight)
			
		bql[0] += bql_category[0]
		bql[1] += bql_category[1]
		bql[2] += bql_category[2]

	return bql

def generate_apartment_cost_matrix(boundaries, sig_digits):
	conn = sqlite3.connect('../data/craigslist.db')
	cursor = conn.cursor()

	query = "SELECT latitude,longitude,price,square_feet FROM apartments WHERE price > 0 AND square_feet > 0"

	cursor.execute(query)

	#Aparently the iterator is consumed, so we just fetch all results here
	cost_raw = cursor.fetchall()
	
	#This will create a negative value for apartments above the price / sqft median
	#and positive for those above it
	cost = [[cost_data[0], cost_data[1], (cost_data[2] / float(cost_data[3])) * 50] for cost_data in cost_raw]

	acm = generate_matrix(boundaries, sig_digits, cost)

	return acm

north_bound = 47.73414
south_bound = 47.50000

east_bound = -122.41936
west_bound = -122.25285

boundaries = [north_bound, south_bound, east_bound, west_bound]

sig_digits = 4


print "Creating apartment cost matrix"
#acl = generate_apartment_cost_list(boundaries, sig_digits)

print "Creating general transit list"
gtl = generate_general_transit_list(boundaries, sig_digits)

print "Creating neighborhood destination transit list"
neighborhoods = ["South Lake Union", "Delridge", "Capitol Hill", "Fremont"]
#ndtl = generate_neighborhood_destination_transit_list(boundaries, neighborhoods)

print "Creating business quality matrix"
categories = [['markets', 20] , ['grocery' , 15] , ['restaurants' , 10] , ['bars' , 5]]
bql = generate_business_quality_list(boundaries, sig_digits, categories)

total = [[], [], []]

total[0] = gtl[0] + bql[0]
total[1] = gtl[1] + bql[1]
total[2] = gtl[2] + bql[2]

hexbin(total[0], total[1], total[2], gridsize=(40,60))
show()


