from math import radians, cos, sin, asin, sqrt

class Haversine(object):
    def __init__(self, regions):
        self.regions = regions

    def _haversine(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371 # Radius of earth in kilometers. Use 3956 for miles
        return c * r

    def calculate_location(self, lat, long):
        locations = list(self.regions.keys())
        distances = list(map(lambda x: (x, self._haversine(lat, long, self.regions[x]['lat'], self.regions[x]['long'])), locations))
        minimum = min(distances, key = lambda d: d[1])
        return minimum[0]


# regions = { "Abruzzo": { "lat": 42.35122196, "long": 13.39843823 },
# "Basilicata": { "lat": 40.63947052, "long": 15.80514834},
# "Calabria":	{ "lat": 38.90597598, "long": 16.59440194 } }

# hav = Haversine(regions)

# reg = hav.calculate_location(37.4460356640154, 13.5672757849516)

# print(reg)
