require './yelp_scraper_api.rb'

require 'rubygems'
require 'oauth'
require 'json'
require 'nokogiri'
require 'open-uri'

$MAX_RESULTS=800

$API_HOST = "api.yelp.com"
$SEARCH_PATH = "/v2/search?"
$LOCATION = "&location=seattle"

$RESTAURANT_PATH = "#{$SEARCH_PATH}category_filter=restaurants#{$LOCATION}"
$FOOD_PATH = $SEARCH_PATH + "category_filter=food" + $LOCATION
$GROCERY_PATH = $SEARCH_PATH + "category_filter=grocery" + $LOCATION
$BARS_PATH = "#{$SEARCH_PATH}category_filter=bars#{$LOCATION}"

def insert_businesses(access_token , business_type , base_path , max_results , base_offset)
	
	for offset in base_offset..max_results

		path = "#{base_path}&offset=#{offset}" 

		business_json_raw = access_token.get(path).body
		business_json = JSON.parse(business_json_raw)
	
		for business in business_json['businesses']

			location = business['location']['address']

			if not location.empty?
				id = business['id']
				rating = business['rating']
				review_count = business['review_count']

				url = business['url']
			
				#Yelp doesn't like this, so move this to a seperate slower daemon later
				#doc = Nokogiri::HTML(open("#{url}"))
				#cost_string = doc.css('span.price-range')[0].text
				#cost = cost_string.length

				puts "#{id}\t#{location}\t#{rating}\t#{review_count}"
			end
		end
	end
end

consumer = OAuth::Consumer.new($consumer_key, $consumer_secret, {:site => "http://#{$API_HOST}"})
access_token = OAuth::AccessToken.new(consumer, $token, $token_secret)

insert_businesses(access_token , "blah" , $RESTAURANT_PATH , 40 , 0)
puts "\n"
insert_businesses(access_token , "blah" , $FOOD_PATH , 40 , 0)
puts "\n"
insert_businesses(access_token , "blah" , $GROCERY_PATH , 40 , 0)
puts "\n"
insert_businesses(access_token , "blah" , $BARS_PATH , 40 , 0)
