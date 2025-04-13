import requests
import math
from database import database_query
from geopy.geocoders import Nominatim

# Takes an FBS Team and returns their schedule for the next year with the following information about each game: Home Team, Away Team, Geographic Coordinates, Neutral Site (bool), and Date.
def get_schedule(team):
    schedule = []
    team_id = database_query.get_id_by_teamname(team).get("ESPN_ID")

    link = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/"+str(team_id)+"/schedule?seasontype=2"

    response = requests.get(link)

    if response.status_code == 200:
        data = response.json()
        events = dict(data).get("events")
        for i in range(len(events)):
            event = events[i]
            schedule.append(get_team_in_schedule(event))
        return(schedule)
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")

# Parses the return value for a game (event) to get the necessary information returned in the get_schedule function.
def get_team_in_schedule(event):
    is_neutral_site = bool(event.get("competitions")[0].get("neutralSite"))
    home = str(event.get("competitions")[0].get("competitors")[0].get("team").get("nickname")).replace("’","")
    away = str(event.get("competitions")[0].get("competitors")[1].get("team").get("nickname")).replace("’","")
    date = event.get("competitions")[0].get("date")
    home_name = database_query.get_teamname_by_nickname(home)
    away_name = database_query.get_teamname_by_nickname(away)

    is_neutral_site = bool(event.get("competitions")[0].get("neutralSite"))

    if home_name == None:
        home_name = "FCS"
    else:
        home_name = home_name.get("TeamName")
    if away_name == None:
        away_name = "FCS"
    else:
        away_name = away_name.get("TeamName")

    if is_neutral_site:
        coords = get_coords_from_loc_name(event.get("competitions")[0].get("venue").get("fullName"))
    elif home_name == "FCS":
        venue = database_query.get_cfb_hfa_by_team(away_name)
        coords = {'latitude':float(venue.get('latitude')), 'longitude': float(venue.get('longitude'))}
    else:
        venue = database_query.get_cfb_hfa_by_team(home_name)
        coords = {'latitude':float(venue.get('latitude')), 'longitude': float(venue.get('longitude'))}
    if (home_name == "FCS" or away_name == "FCS"):
        pass
    else: # DOES SCHEDULE
        #print(predict_score_sp_plus(away=away_name,home=home_name))
        pass

    return {"Away": away_name, "Home": home_name, "Lat": coords.get('latitude'), "Lng": coords.get('longitude'), "Neutral": is_neutral_site, "Date": date}

# Converts Venue Names into geographic coordinates, only used in Neutral Site Games or Games at FCS Stadiums (if there are any).
def get_coords_from_loc_name(location):
    if "at " in location: # Fixes locations of format {Name} Field at {Name} Stadium
        location = location.split("at ")[1]
    geolocator = Nominatim(user_agent="http")
    location = geolocator.geocode(location)
    return({"latitude": location.latitude, "longitude": location.longitude})

# Calculates Distance between teams in miles, for travel effects
def calculate_distance_in_miles(away_team, home_team, neutral, lat, lng):
    home_hfa = database_query.get_cfb_hfa_by_team(home_team)
    away_hfa = database_query.get_cfb_hfa_by_team(away_team)

    home_lat = float(home_hfa.get("latitude"))
    home_long = float(home_hfa.get("longitude"))
    away_lat = float(away_hfa.get("latitude"))
    away_long = float(away_hfa.get("longitude"))

    if neutral:
        home_lat = lat
        home_long = lng

    #print(home_lat)

    R = 3958.8  # Radius of the Earth in miles

    lat1_rad = math.radians(home_lat)
    lon1_rad = math.radians(home_long)
    lat2_rad = math.radians(away_lat)
    lon2_rad = math.radians(away_long)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance