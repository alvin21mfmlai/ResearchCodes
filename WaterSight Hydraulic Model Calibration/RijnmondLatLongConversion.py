from pyproj import Transformer

# Convert feet to meters
rd_x_ft = 241860.74 ## change x coordinate
rd_y_ft = 1412814.92 ## change y coordinate

rd_x_m = rd_x_ft * 0.3048
rd_y_m = rd_y_ft * 0.3048

# Define the transformer
transformer = Transformer.from_crs("epsg:28992", "epsg:4326")

# Convert to WGS84 (lat, long)
lat, lon = transformer.transform(rd_x_m, rd_y_m)

print(f"Latitude: {lat}, Longitude: {lon}")
