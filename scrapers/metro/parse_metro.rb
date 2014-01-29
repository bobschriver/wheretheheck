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
			routes_insert_sql += "insert into routes (route_id,route_number) values (#{route_id}, \"#{route_number}\");"
		else
			#Ignore first line of file
			routes_first_line = false
		end
	end

	$db.execute_batch(routes_insert_sql)

	p "Inserted Routes"
end

insert_routes()

