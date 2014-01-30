require 'nokogiri'
require 'sqlite3'
require 'open-uri'

apartments_url = "http://seattle.craigslist.org/see/apa/"

db = SQLite3::Database.new( "../../data/craigslist.db" )

apartment_doc = Nokogiri::HTML(open("#{apartments_url}"))

listings = apartment_doc.css("p.row")

sql = ""

for listing in listings
		
	pid = listing['data-pid'].to_i

	latitude = listing['data-latitude'].to_f
	longitude = listing['data-longitude'].to_f

	if not latitude.eql? 0.0 and not longitude.eql? 0.0
		url = listing.at_css("a.i")['href']
		price_element = listing.at_css("span.price")	
		size_element = listing.at_css("span.l2")

		#p size_element

		if not price_element.nil? and not size_element.nil?
			neighborhood_element = listing.at_css("small")
			neighborhood_string = ""
			
			if not neighborhood_element.nil?
				neighborhood_string = neighborhood_element.text
			end

			price_string = price_element.children[0].text
			size_string = size_element.children[2].text

			price = price_string.delete('$').to_i	

			bedrooms_match = /(\d)br/.match(size_string)
			sqft_match = /(\d+)ft/.match(size_string)
	
			#We probably only need bedrooms, but we should have enough data anyway
			if not bedrooms_match.nil?
				#For some reason the match data is stored at the second index
				#Ruby 1.8.7 regex blows
				bedrooms = bedrooms_match[1].to_i
				
			else
				bedrooms = 0
			end
			
			#Ignore is for matching pid's
			if not sqft_match.nil?
				sqft = sqft_match[1].to_i
			else	
				sqft = 0
			end

			sql += "insert or ignore into apartments (pid, url, longitude, latitude, price, bedrooms, square_feet, neighborhood_string) values (#{pid}, '#{url}', #{longitude}, #{latitude}, #{price}, #{bedrooms}, #{sqft}, '#{neighborhood_string}');"
		end
	end
end

p sql

db.execute_batch(sql)
