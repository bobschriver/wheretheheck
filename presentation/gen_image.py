import sqlite3
import numpy
import scipy

from numpy import ones,zeros,convolve,median
from scipy.misc import imsave
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

north_bound = 47.73414
south_bound = 47.50000

east_bound = -122.41936
west_bound = -122.25285

boundaries = [north_bound, south_bound, east_bound, west_bound]

sig_digits = 4

gtm = generate_general_transit_matrix(boundaries, sig_digits)

gtm_norm = gtm * (255 / (median(gtm[gtm > 0])))

gtm_norm[gtm_norm > 255] = 255

imsave("gtm_norm.jpg", uniform_filter(gtm_norm, 10))

neighborhoods = ["South Lake Union", "Wallingford"]

ndtm = generate_neighborhood_destination_transit_matrix(boundaries, sig_digits, neighborhoods)

imsave("ndtm_norm.jpg", uniform_filter(ndtm, 10))

gtm_ndtm = gtm

gtm_ndtm_norm = gtm_ndtm * (255 / (median(gtm_ndtm[gtm_ndtm > 0])))

gtm_ndtm_norm[gtm_ndtm_norm > 255] = 255

gtm_ndtm_norm += ndtm

imsave("gtm_ndtm_norm.jpg", uniform_filter(gtm_ndtm_norm, 10))
