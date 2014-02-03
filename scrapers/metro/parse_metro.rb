require 'sqlite3'

$db = SQLite3::Database.new( "../../data/busses.db" )

def insert_routes
	routes_file = File.open('./metro_data/routes.txt').read

	routes_first_line = true
	routes_insert_sql = ""

	routes_file.each_line do |route_string|
		if not routes_first_line
			route_arr = route_string.split(',')
			route_id = route_arr[0].delete("\"").to_i
			route_number = route_arr[2].delete("\"")
		
			#Yes I know I just deleted the quotes
			routes_insert_sql += "insert into routes (route_id,route_number) values (#{route_id}, '#{route_number}');"
		else
			#Ignore first line of file
			routes_first_line = false
		end
	end

	$db.execute_batch(routes_insert_sql)

	p "Inserted Routes"
end

def insert_stops
	trips_file = File.open('./metro_data/trips.txt')

	trips_first_line = true

	trip_route_map = Hash.new

	trips_file.each_line do |trip_string|
		if not trips_first_line
			trip_arr = trip_string.split(',')
			route_id = trip_arr[0].delete("\"").to_i
			trip_id = trip_arr[2].delete("\"").to_i

			if trip_route_map.key? trip_id
				p "#{trip_id} #{route_id}"
			end

			trip_route_map[trip_id] = route_id
		else
			#Ignore first line of file
			trips_first_line = false
		end
	end

	stop_times_file = File.open('./metro_data/stop_times.txt').read

	stop_times_first_line = true

	stop_route_map = Hash.new
	
	stop_count_map = Hash.new

	stop_times_file.each_line do |stop_time_string|
		if not stop_times_first_line
			stop_time_arr = stop_time_string.split(',')
			trip_id = stop_time_arr[0].delete("\"").to_i
			stop_id = stop_time_arr[3].delete("\"").to_i

			route_id = trip_route_map[trip_id]
			
			#if route_count_map.key? route_id
			#	route_count_map[route_id] += 1
			#else 
			#	route_count_map[route_id] = 1
			#end
			
			if stop_count_map.key? stop_id
				stop_count_map[stop_id] += 1
			else
				stop_count_map[stop_id] = 1
			end
			
			stop_route_map[stop_id] = route_id
		else
			#Ignore first line of file
			stop_times_first_line = false
		end
	end

	stops_file = File.open('./metro_data/stops.txt').read

	stops_first_line = true

	stops_sql = ""

	stops_file.each_line do |stop_string|
		if not stops_first_line	
			stop_arr = stop_string.split(',')
			stop_id = stop_arr[0].delete("\"").to_i
			
			stop_lat = stop_arr[4].delete("\"").to_f
			stop_long = stop_arr[5].delete("\"").to_f
		
			stop_desc = stop_arr[2].delete("\"")

			west_long = -122.45969
			east_long = -122.24676

			north_lat = 47.73414
			south_lat = 47.5

			if stop_long.between?(west_long, east_long) and stop_lat.between?(south_lat, north_lat)
				stops_sql += "insert or ignore into stops (stop_id, latitude, longitude, trips_count) values (#{stop_id}, #{stop_lat}, #{stop_long}, #{stop_count_map[stop_id]});"
				stops_sql += "insert into route_stop (route_id, stop_id) values (#{stop_route_map[stop_id]}, #{stop_id});"
			end
		else 
			stops_first_line = false
		end
	end

	$db.execute_batch(stops_sql)
end

#insert_routes()

insert_stops()
