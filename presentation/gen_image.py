import sqlite3
import numpy
import scipy

from numpy import zeros
from scipy.misc import imsave
from scipy.ndimage.filters import *

def generate_general_transit_matrix(north_bound, south_bound, east_bound, west_bound, sig_digits):
	sig_digits_shift = 10 ** sig_digits
	
	height = int((north_bound - south_bound) * sig_digits_shift) 
	width = int(abs(east_bound - west_bound) * sig_digits_shift)

	print height, width

	gtm = zeros((width, height))

	conn = sqlite3.connect('../data/busses.db')
	cursor = conn.cursor()

	stops = cursor.execute("select latitude,longitude,trips_count from stops")

	for stop in stops:
		latitude = stop[0]
		longitude = stop[1]
		trips_count = stop[2]

		if (north_bound > latitude > south_bound) and (west_bound > longitude > east_bound):
			x_index = int(abs(longitude - west_bound) * sig_digits_shift)
			y_index = int((north_bound - latitude) * sig_digits_shift)

			gtm[x_index, y_index] += trips_count
	
	gtm_filtered = gaussian_filter(gtm, 2)
	return gtm_filtered

north_bound = 47.73414
south_bound = 47.50000

east_bound = -122.41936
west_bound = -122.25285

gtm = generate_general_transit_matrix(north_bound, south_bound, east_bound, west_bound, 4)

print gtm.max()

gtm *= 255/gtm.max()

imsave("gtm_norm.jpg", gtm)
