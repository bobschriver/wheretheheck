import sqlite3
import numpy
import scipy
import matplotlib.pyplot
import matplotlib.cm

from matplotlib.cm import jet
from matplotlib.pyplot import hexbin,show
from numpy import ones,zeros,convolve,median,dstack
from scipy.misc import imsave,imread,imresize
from scipy.ndimage.filters import *

def modify_lat_long_to_x_y(boundaries, sig_digits, data_list):
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

	gtl = modify_lat_long_to_x_y(boundaries, sig_digits, stops)

	return gtl

def generate_neighborhood_destination_transit_matrix(boundaries, sig_digits, neighborhoods):
	conn = sqlite3.connect('../data/busses.db')
	cursor = conn.cursor()

	placeholders = ', '.join('?' * len(neighborhoods))

	query = "SELECT latitude,longitude,255 FROM stops WHERE stop_id IN (SELECT stop_id FROM route_stop WHERE route_id IN (SELECT route_id FROM neighborhood_route WHERE neighborhood_id IN (SELECT neighborhood_id FROM neighborhoods WHERE neighborhood_name IN (%s))))" % placeholders

	stops = cursor.execute(query, neighborhoods)

	ndtm = generate_matrix(boundaries, sig_digits, stops)
	
	return ndtm

def generate_business_quality_matrix_for_category(boundaries, sig_digits, category):
	conn = sqlite3.connect('../data/yelp.db')
	cursor = conn.cursor()

	query = "SELECT latitude, longitude, rating, num_ratings FROM businesses WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND yelp_id IN (SELECT yelp_id FROM business_category WHERE category_id = (SELECT category_id FROM categories WHERE category_name=?))"

	quality_raw = cursor.execute(query , [category])

	quality = [[quality_data[0], quality_data[1], quality_data[2] * quality_data[3]] for quality_data in quality_raw]
	
	bqm = generate_matrix(boundaries, sig_digits, quality)
	
	return bqm

def generate_business_quality_matrix(boundaries, sig_digits, categories):
	#This just generates a zeros matrix
	bqm = generate_matrix(boundaries, sig_digits, [])

	for category,category_weight in categories:
		bqm_category = generate_business_quality_matrix_for_category(boundaries, sig_digits, category)
		#Will cache these and apply weights dynamically in the future
		#imsave(category + ".tiff", bqm_category)

		print "Creating %s business quality matrix" % category
		bqm_category_norm = normalize_image(bqm_category)
		imsave(category + ".tiff", gaussian_filter(bqm_category_norm, 10))
		
		bqm += bqm_category_norm * category_weight

	return bqm

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
print len(gtl[0]),len(gtl[1]),len(gtl[2])
hexbin(gtl[0], gtl[1], gtl[2], gridsize=(40,60), cmap=jet)
show()

print "Creating neighborhood destination transit list"
neighborhoods = ["South Lake Union", "Delridge", "Capitol Hill", "Fremont"]
#ndtl = generate_neighborhood_destination_transit_list(boundaries, neighborhoods)

print "Creating business quality matrix"
categories = [['markets', 20] , ['grocery' , 15] , ['restaurants' , 10] , ['bars' , 5]]
#bql = generate_business_quality_list(boundaries, categories)


