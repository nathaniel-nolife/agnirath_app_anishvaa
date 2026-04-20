import requests
import pandas as pd
import math

def get_distance(lat1, lon1, lat2, lon2):
    R = 6371000 
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    a = math.sin(math.radians(lat2 - lat1)/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(math.radians(lon2 - lon1)/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def get_bearing(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
    return (math.degrees(math.atan2(x, y)) + 360) % 360

start = (27.8277, -26.8195) # Sasolburg
end = (26.0753, -25.5369)   # Zeerust

#map the route
url = f"http://router.project-osrm.org/route/v1/driving/{start[0]},{start[1]};{end[0]},{end[1]}?overview=full&geometries=geojson"
route_coords = requests.get(url).json()['routes'][0]['geometry']['coordinates']

sampled = [route_coords[0]]
for pt in route_coords[1:]:
    if get_distance(sampled[-1][1], sampled[-1][0], pt[1], pt[0]) >= 200:
        sampled.append(pt)

# retrieve Altitude
elevations = []
chunk_size = 10
for i in range(0, len(sampled), chunk_size):
    chunk = sampled[i:i + chunk_size]
    lats = ",".join([str(p[1]) for p in chunk])
    lons = ",".join([str(p[0]) for p in chunk])
    res = requests.get(f"https://api.open-meteo.com/v1/elevation?latitude={lats}&longitude={lons}")
    elevations.extend(res.json()['elevation'])

# compute Slope and Direction
data = []
for i in range(len(sampled)):
    lon, lat = sampled[i]
    alt = elevations[i]
    
    if i == 0:
        slope, bearing = 0.0, 0.0
    else:
        prev_lon, prev_lat = sampled[i-1]
        dist = get_distance(prev_lat, prev_lon, lat, lon)
        slope = (alt - elevations[i-1]) / dist if dist > 0 else 0.0
        bearing = get_bearing(prev_lat, prev_lon, lat, lon)

    data.append({
        "Latitude": lat,
        "Longitude": lon,
        "Altitude": alt,
        "Direction": round(bearing, 2),
        "Slope": round(slope, 5)
    })

#save to CSV
df = pd.DataFrame(data)
df.to_csv("route_data.csv", index=False)
print("Data successfully saved to route_data.csv")