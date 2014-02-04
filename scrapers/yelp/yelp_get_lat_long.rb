require 'sqlite3'
require 'json'
require 'open-uri'

geocode_url_base = "http://maps.googleapis.com/maps/api/geocode/json?"

yelp_db = SQLite3::Database.new("../../data/yelp.db")

businesses = yelp_db.execute("select restaurant_id,location from business where latitude is NULL and longitude is NULL");

for address_id_pair in businesses
	business_id = address_id_pair[0]
	address_url_safe = address_id_pair[1].gsub(" ", "+")

	geocode_url = "#{geocode_url_base}address=#{address_url_safe}+Seattle+WA&sensor=false"

	geocode_json = JSON.parse(open(geocode_url).read)
	
	if geocode_json['status'].eql? "OK"
		latitude = geocode_json['results'].first['geometry']['location']['lat']
		longitude = geocode_json['results'].first['geometry']['location']['lng']

		sql = "update business set latitude=#{latitude},longitude=#{longitude} where restaurant_id=#{business_id}"
		yelp_db.execute(sql)
		p "Inserted #{latitude} #{longitude} for #{business_id} at #{address_url_safe}"

		sleep(40)
	end
end
