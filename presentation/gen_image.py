import sqlite3
import numpy
import scipy

from numpy import ones,zeros,convolve,median
from scipy.misc import imsave,imread,imresize
from scipy.ndimage.filters import *

def generate_matrix(boundaries, sig_digits, data_list):
	north_bound = boundaries[0]
	south_bound = boundaries[1]
	east_bound = boundaries[2]
	west_bound = boundaries[3]

	sig_digits_shift = 10 ** sig_digits
	
	height = int((north_bound - south_bound) * sig_digits_shift) 
	width = int(abs(east_bound - west_bound) * sig_digits_shift)

	matrix = zeros((height, width))

	for data in data_list:
		latitude = data[0]
		longitude = data[1]
		value = data[2]
	
		if (north_bound > latitude > south_bound) and (west_bound > longitude > east_bound):
			x_index = int(abs(longitude - east_bound) * sig_digits_shift)
			y_index = int((north_bound - latitude) * sig_digits_shift)

			matrix[y_index, x_index] += value
	
	return matrix

def generate_general_transit_matrix(boundaries, sig_digits):
	conn = sqlite3.connect('../data/busses.db')
	cursor = conn.cursor()

	stops = cursor.execute("select latitude,longitude,trips_count from stops")

	gtm = generate_matrix(boundaries, sig_digits, stops)

	return gtm

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

		#TODO: Normalize
		bqm_category_weighted = bqm_category * category_weight
		imsave(category + ".tiff", gaussian_filter(bqm_category_weighted, 10))
		
		bqm += bqm_category_weighted

	return bqm

north_bound = 47.73414
south_bound = 47.50000

east_bound = -122.41936
west_bound = -122.25285

boundaries = [north_bound, south_bound, east_bound, west_bound]

sig_digits = 4

print "Creating general transit matrix"
gtm = generate_general_transit_matrix(boundaries, sig_digits)
gtm_norm = gtm * (255 / (median(gtm[gtm > 0])))
gtm_norm[gtm_norm > 255] = 255
imsave("gtm_norm.tiff", gaussian_filter(gtm_norm, 10))

print "Creating neighborhood destination transit matrix"
neighborhoods = ["South Lake Union", "Wallingford"]
ndtm = generate_neighborhood_destination_transit_matrix(boundaries, sig_digits, neighborhoods)
imsave("ndtm_norm.tiff", gaussian_filter(ndtm, 10))

print "Creating business quality matrix"
categories = [['markets', 5] , ['grocery' , 4] , ['restaurants' , 3] , ['bars' , 1]]
bqm = generate_business_quality_matrix(boundaries, sig_digits, categories)
bqm_norm = bqm * (255 / (median(bqm[bqm > 0])))
bqm_norm[bqm_norm > 255] = 255
imsave("bqm_norm.tiff", gaussian_filter(bqm_norm , 10))

print "Creating final image"
total_norm = gtm_norm + ndtm + bqm_norm
imsave("total.tiff", gaussian_filter(total_norm, 10))
