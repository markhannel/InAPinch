# Data Collection.

Data collection is tantamount to this project! To provide statistically-backed
route reccomendations that incorporates multiple modes of transportation, we
will require the following data for each mode of transport:
- geospatial information (where is each **active** station)
- historical trip information (how long does each trip take, how long is the wait period at this location).
- Live-feed information if we want to give precise in the moment data.
- If trip length varies amongst a demographic, sufficient data to make
reasonable estimates.

# Modules.
download.py queries the live MTA Feed and live Citibike feed to gather a list of station
locations. Historical MTA data is collected from the MTA developer archives.
Historical Citi Bike dock data was downloaded by hand from TheOpenBus.

aggregate.py collects the data sourced from TheOpenBus.com into one file.

To learn about the historical MTA Data source:
http://web.mta.info/developers/MTA-Subway-Time-historical-data.html

General MTA information (Incomplete):
- http://web.mta.info/developers/developer-data-terms.html#data

MTA Subway data sources:
- Historical subway arrival data: http://web.mta.info/developers/data/archives.html


MTA Bus data sources:
- Historical bus arrival data: https://www.theopenbus.com/raw-data.html

Motivate (Citi Bike) data sources:
- Historical station occupancy data https://www.theopenbus.com/raw-data.html

NYC Ferry data sources: