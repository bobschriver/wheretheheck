require 'nokogiri'
require 'sqlite3'
require 'open-uri'

apartments_url = "http://seattle.craigslist.org/see/apa/"

apartment_doc = Nokogiri::HTML(open("#{apartments_url}"))

listings = apartment_doc.css("p.row")

for listing in listings
		
	pid = listing['data-pid']

	latitude = listing['data-latitude']
	longitude = listing['data-longitude']

	if not latitude.nil? and not longitude.nil? 
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
			
			bedrooms_match = /(\d)br/.match(size_string)
			sqft_match = /(\d+)ft/.match(size_string)
	
			#We probably only need bedrooms, but we should have enough data anyway
			if not bedrooms_match.nil?
				#For some reason the match data is stored at the second index
				#Ruby 1.8.7 regex blows
				bedrooms = bedrooms_match[1].to_i
				
				if not sqft_match.nil?
					sqft = sqft_match[1].to_i
				end

				p "Lat #{latitude} Long #{longitude} Price #{price_string} BR #{bedrooms} SQFT #{sqft} Neighborhood #{neighborhood_string}"
			end
		end
	end
end
