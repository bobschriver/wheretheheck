WheretheHeck
============

#Overview

WheretheHeck (WtH) generates and presents a heatmap overlay for a city (currently Seattle), which indicates desireable areas based on user criteria.
Examples of these criteria would be frequent transit, transit to specific neighborhoods, cheap housing, high-quality grocery etc.
WtH can be considered a sort of reverse Walkscore, which shows areas in a city where someone should look to live.

WtH consists of three components:

+Data Obtainting
+Image Creating
+Image Presenting

#Data Obtainting

First, the data WtH requires is scraped/grabbed from King County Metro, Yelp, and Craigslist. Some of these scrapers are run once (King Country Metro), and some are run continuously (Craigslist). This data all revolves around lat-long coordinates, so that all entities can eventually be mapped. Also important is coming up with a quality metric for all data, for Metro data this is frequency, Craigslists apartments as cost per sqft, etc.

#Image Creating

We consider the city as a matrix, with each index corresponding to a latitude and longitude and value corresponding to the weight for each point. Each metic we care about (transportation, quality bars, etc) have their own matrix. Most of these matrices do not change between requests, so we can cache them. The user supplied weights are then multiplied into the appropriate matrix, and all matrices are normalized and added together to form a fina
#Image Presenting

The client will take the user's weights, and return the heatmap image.
