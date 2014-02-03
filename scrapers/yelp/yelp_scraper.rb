require './yelp_scraper_api.rb'

require 'rubygems'
require 'oauth'
require 'json'
require 'nokogiri'
require 'open-uri'
require 'sqlite3'

max_results = 800

api_host = "api.yelp.com"
search_path = "/v2/search?"

categories = ["grocery" , "bars" , "restaurants" , "food"]

#Need to convert from metro neighborhoods to yelp neighborhoods. Only a few need to be modified
#So we just do it here rather than having a seperate table. todo
neighborhood_replacements = { 
	"Admiral District" => "Admiral",
	"West Seattle Junction" => "Junction"
}

neighborhoods_db = SQLite3::Database.new("../../data/busses.db")

neighborhoods = neighborhoods_db.execute("select (neighborhood_name) from neighborhoods").map do |neighborhood_name|
	if neighborhood_replacements.key? neighborhood_name[0]
		neighborhood_replacements[neighborhood_name[0]] 
	else
		#Have to convert spaces to +'s for the yelp url to be valid
		neighborhood_name[0].gsub(" ", "+")
	end
end

neighborhoods.shuffle!

$yelp_db = SQLite3::Database.new("../../data/yelp.db")

def insert_businesses(access_token , base_path , max_results , base_offset, category, business_filter)
	
	#Step through 20 (max yelp allows) results at a time
	for offset in (base_offset..max_results).step(20)
		path = "#{base_path}&offset=#{offset}" 

		p "Inserting for  #{path}"
		business_json_raw = access_token.get(path).body
		business_json = JSON.parse(business_json_raw)

		sql = ""

		for business in business_json['businesses']

			location = business['location']['address']

			if not location.empty?
				id = business['id']
				
				#Yelp returns a 0-5 with .5 increments, I just want an integer
				rating = (business['rating'].to_f * 2).to_i
				review_count = business['review_count'].to_i

				url = business['url']
			
				#Could do two seperate inserts here rather than passing the category as a parameter
				sql += "insert or ignore into business (yelp_id, category, rating, num_ratings, location, url) values ('#{id}', '#{category}', #{rating}, #{review_count}, '#{location.first.gsub("'", "")}', '#{url}');"
			end
		end
		
		$yelp_db.execute_batch(sql)
		
		p "Inserted #{base_path}"
	end
end

consumer = OAuth::Consumer.new($consumer_key, $consumer_secret, {:site => "http://#{api_host}"})
access_token = OAuth::AccessToken.new(consumer, $token, $token_secret)

for category in categories
	for neighborhood in neighborhoods

		base_path = "#{search_path}category_filter=#{category}&location=#{neighborhood}+Seattle"
		#We go up to 39 so we just get two pages of results
		insert_businesses(access_token , base_path, 39, 0, category, "")
		#Gotta stay under that daily request cap
		sleep(30)
	end
end

