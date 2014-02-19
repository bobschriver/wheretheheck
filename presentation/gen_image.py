import sqlite3
import numpy
import scipy
import matplotlib.pyplot

from matplotlib.pyplot import get_cmap
from numpy import ones,zeros,convolve,median,dstack
from scipy.misc import imsave,imread,imresize
from scipy.ndimage.filters import *

def normalize_image(image, image_median):
	norm_image = image * (image_median / (median(image[image > 0])))
	norm_image[norm_image > 128] = 128

	return norm_image

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

	query = "SELECT latitude,longitude,64 FROM stops WHERE stop_id IN (SELECT stop_id FROM route_stop WHERE route_id IN (SELECT route_id FROM neighborhood_route WHERE neighborhood_id IN (SELECT neighborhood_id FROM neighborhoods WHERE neighborhood_name IN ({0}))))".format(placeholders)

	stops = cursor.execute(query, neighborhoods)

	ndtm = generate_matrix(boundaries, sig_digits, stops)
	
	return ndtm

def generate_business_quality_matrix_for_category(boundaries, sig_digits, category):
	conn = sqlite3.connect('../data/yelp.db')
	cursor = conn.cursor()

	query = "SELECT latitude, longitude,rating FROM businesses WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND num_ratings > 25 AND num_ratings < 250 AND rating > 6 AND yelp_id IN (SELECT yelp_id FROM business_category WHERE category_id = (SELECT category_id FROM categories WHERE category_name=?))"

	quality= cursor.execute(query , [category])

	bqm = generate_matrix(boundaries, sig_digits, quality)
	
	return bqm

def generate_business_quality_matrix(boundaries, sig_digits, categories):
	#This just generates a zeros matrix
	bqm = generate_matrix(boundaries, sig_digits, [])

	for category,category_weight in categories:
		bqm_category = generate_business_quality_matrix_for_category(boundaries, sig_digits, category)

		print("Creating {0} business quality matrix".format(category))
		bqm_category_filtered = gaussian_filter(bqm_category, 10)
		imsave(category + ".tiff", bqm_category_filtered)

		bqm += bqm_category * category_weight

	return bqm

def generate_apartment_cost_matrix(boundaries, sig_digits):
	conn = sqlite3.connect('../data/craigslist.db')
	cursor = conn.cursor()

	query = "SELECT latitude,longitude,price,square_feet FROM apartments WHERE price > 0 AND square_feet > 0"

	cursor.execute(query)

	#Aparently the iterator is consumed, so we just fetch all results here
	cost_raw = cursor.fetchall()
	
	prices_per_sqft = [cost_data[2] / float(cost_data[3]) for cost_data in cost_raw]
	prices_per_sqft_median = median(prices_per_sqft)

	#This will create a negative value for apartments above the price / sqft median
	#and positive for those above it
	cost = [[cost_data[0], cost_data[1], (prices_per_sqft_median - (cost_data[2] / float(cost_data[3]))) * 48] for cost_data in cost_raw]

	acm = generate_matrix(boundaries, sig_digits, cost)

	return acm

north_bound = 47.73414
south_bound = 47.50000

east_bound = -122.41936
west_bound = -122.25285

boundaries = [north_bound, south_bound, east_bound, west_bound]

sig_digits = 4

print("Creating apartment cost matrix")
acm = generate_apartment_cost_matrix(boundaries, sig_digits)
acm_filtered = gaussian_filter(acm , 20)
imsave("acm.tiff", acm_filtered)

print("Creating general transit matrix")
gtm = generate_general_transit_matrix(boundaries, sig_digits)
gtm_norm = normalize_image(gtm, 64)
gtm_norm_filtered = gaussian_filter(gtm_norm, 10)
imsave("gtm_norm.tiff", gtm_norm_filtered)

print("Creating neighborhood destination transit matrix")
neighborhoods = ["South Lake Union", "Delridge"]
ndtm = generate_neighborhood_destination_transit_matrix(boundaries, sig_digits, neighborhoods)
ndtm_filtered = gaussian_filter(ndtm, 15)
imsave("ndtm_norm.tiff", ndtm_filtered)

print("Creating business quality matrix")
categories = [['markets', 25] , ['grocery' , 20] , ['restaurants' , 15] , ['bars' , 10]]
bqm = generate_business_quality_matrix(boundaries, sig_digits, categories)
imsave("bqm_norm.tiff", bqm)

cmap = get_cmap('jet')

print("Creating final image")
total_norm = gtm_norm_filtered + ndtm_filtered + bqm + acm_filtered
imsave("total.png", cmap(gaussian_filter(total_norm, 10)))
