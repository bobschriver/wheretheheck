require 'nokogiri'
require 'open-uri'
require 'sqlite3'

db = SQLite3::Database.new( "../../data/busses.db" )

url = "http://metro.kingcounty.gov/schedules/neighborhoods.asp"

transit_center_neighborhood_map = {
	"Genesee Hill" => "West Seattle Junction",
	"Beach Dr. SW" => "Admiral District",
	"Harbor Ave SW" => "Admiral District",
	"West Seattle" => "West Seattle Junction",
	"35th Ave SW" => "West Seattle Junction",
	"Westwood Village" => "Roxhill",
	"Westwood Town Center" => "Roxhill",
	"Stadium Station (Link)" => "SoDo",
	"Blue Ridge" => "North Beach",
	"Downtown Seattle" => "Downtown",
	"Seattle Pacific University" => "Queen Anne",
	"Dexter Ave N" => "Westlake",
	"North Seattle Community College" => "Licton Springs",
	"Government Locks" => "Ballard",
	"UW Campus" => "University District",
	"Harborview Hospital" => "First Hill",
	"Pacific Medical Center" => "First Hill",
	"Beacon Hill Station (Link)" => "Beacon Hill",
	"Tunnel (Link)" => "Downtown",
	"Downtown Tunnel Station" => "Downtown",
	"SODO" => "SoDo",
	"Sodo" => "SoDo",
	"SODO Station (Link)" => "SoDo",
	"Rainier Beach Station (Link)" => "Rainier Beach",
	"Woodland Park Zoo" => "Phinney Ridge",
	"Seattle Center West" => "Lower Queen Anne",
	"West Queen Anne" => "Interbay",
	"Seattle Center East" => "Lower Queen Anne",
	"East Queen Anne" => "Queen Anne",
	"Othello Station (Link)" => "Rainier Valley",
	"Columbia City Station (Link)" => "Columbia City",
	"East Madison St" => "Capitol Hill",
	"Seattle Central Community College" => "Capitol Hill",
	"Mount Baker Transit Center" => "Mount Baker",
	"East Yesler Way" => "Central District",
	"Colman Park" => "Mount Baker",
	"Group Health Hospital" => "Capitol Hill",
	"Green Lake P&R" => "Green Lake",
	"Broadway" => "Capitol Hill",
	"White Center Transfer Point" => "White Center",
	"Highline Specialty Medical Center" => "Highline",
	"Federal Center South" => "SoDo",
	"West Green Lake" => "Green Lake",
	"East Green Lake" => "Green Lake",
	"University Village" => "University District",
	"Northgate Transit Center" => "Northgate",
	"Northgate Mall" => "Northgate",
	"Latona Ave NE" => "Wallingford",
	"Aurora Ave. N" => "Wallingford",	
	"Aurora Ave. N." => "Wallingford",
	"U-District" => "University District",
	"Mount Baker Station (Link)" => "Mount Baker",
	"Seattle Center" => "Lower Queen Anne",
	"North Queen Anne Hill" => "Queen Anne",
	"Wedgewood" => "Wedgwood",
	"Northwest Hostpital" => "Haller Lake"
}


neighborhoods_id = db.execute("select neighborhood_name,neighborhood_id from neighborhoods")

#Not exactly sure why this asterisk has to be here...
neighborhoods_id_map = Hash[*neighborhoods_id.flatten]

routes_id = db.execute("select route_number,route_id from routes")

routes_id_map = Hash[*routes_id.flatten]


doc = Nokogiri::HTML(open("#{url}")) do |config|
	config.noblanks
end

inner_bound = doc.at_css('.alpha').at_css('div')

inner_bound.children.each_slice(4) do |first_blank, header, second_blank, content|
	if first_blank.nil? or header.nil? or second_blank.nil? or content.nil?
		break
	end

	neighborhood_global = header.at_css('a').text.strip

	p neighborhood_global

	route_number_elements = content.css('div.route_number')
	neighborhood_elements = content.css('p')

	route_number_strings = route_number_elements.map do |route_number_element| 
		route_number_element.at_css('a').text.strip
	end

	neighborhoods_strings = neighborhood_elements.map do |neighborhood_element| 
		neighborhood_element.children.first.text
	end

	route_neighborhoods_pairs = route_number_strings.zip(neighborhoods_strings)

	p route_neighborhoods_pairs

	for route_neighborhoods_pair in route_neighborhoods_pairs
		route_number = route_neighborhoods_pair[0]
		route_id = routes_id_map[route_number]

		if not route_id.nil?

			neighborhoods_string = route_neighborhoods_pair[1]

			#Contains all of the "neighborhoods" listed as serviced by the metro website
			neighborhoods_arr = neighborhoods_string.split(",")
			neighborhoods_arr.push(neighborhood_global)

			neighborhood_route_sql = ""
			found_neighborhood_for_route = false

			for neighborhood in neighborhoods_arr

				neighborhood.strip!

				#Could be nil
				neighborhood_from_tc = transit_center_neighborhood_map[neighborhood]

				if not neighborhood_from_tc.nil?
					neighborhood = neighborhood_from_tc
				end

				neighborhood_id = neighborhoods_id_map[neighborhood]

				if not neighborhood_id.nil?
					found_neighborhood_for_route = true
					neighborhood_route_sql += "insert into neighborhood_route (neighborhood_id,route_id) values (#{neighborhood_id},#{route_id});";
				end
			end

			if found_neighborhood_for_route
				db.execute_batch(neighborhood_route_sql)

				p "Inserted for route #{route_number}:#{route_id}"
			end
		end
	end
end
