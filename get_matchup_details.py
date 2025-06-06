import requests
import math

from datetime import datetime
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
    game_id = event.get("competitions")[0].get("id")
    home = str(event.get("competitions")[0].get("competitors")[0].get("team").get("nickname")).replace("’","")
    away = str(event.get("competitions")[0].get("competitors")[1].get("team").get("nickname")).replace("’","")
    date = event.get("competitions")[0].get("date")
    week = event.get("week").get("number")
    home_name = database_query.get_teamname_by_nickname(home)
    away_name = database_query.get_teamname_by_nickname(away)
    #home_score = event.get("competitions"[0].get("competitors"[0].get("score").get("value")))
    #away_score = event.get("competitions"[0].get("competitors"[0].get("score").get("value")))

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

    return {"ID":game_id, "Away": away_name, "Home": home_name, "Lat": coords.get('latitude'), "Lng": coords.get('longitude'), "Neutral": is_neutral_site, "Date": date, "Week": week}

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

# Get the score adjustment from travel and rest effects for a whole schedule 
def get_game_information(team):
    output = []
    schedule = get_schedule(team)
    distance = 0
    last_game = ''
    for i in range(len(schedule)):
        event = schedule[i]
        team_rest = get_rest(event, last_game)
        is_neutral_site = bool(event.get("Neutral"))
        # Determines who the opponent is
        home = False
        opp = event.get("Home")
        if(opp == team):
            opp = event.get("Away")
            home = True
        # Excludes distance traveled by FCS teams and home games from distance calculation
        if (event.get('Home') == team or event.get('Home') == "FCS") and not is_neutral_site:
            if(event.get('Away') == "FCS"):
                opp_stuff = [distance,team_rest]
            else:
                opp_stuff = get_opp_distance_in_schedule(opp, team)
            event = add_dist_and_rest_dict(home, event,distance,team_rest,opp_stuff)
        # Calculates Neutral site distance traveled
        elif (event.get('Home') == team and is_neutral_site):
            added_dist = calculate_distance_in_miles(event.get("Home"),event.get("Home"),is_neutral_site,event.get("Lat"),event.get("Lng"))
            distance += added_dist
            opp_stuff = get_opp_distance_in_schedule(opp, team)
            event = add_dist_and_rest_dict(home, event,distance,team_rest,opp_stuff)
            distance += added_dist
        # Calculates standard away distance traveled
        else:
            added_dist = calculate_distance_in_miles(event.get("Away"),event.get("Home"),is_neutral_site,event.get("Lat"),event.get("Lng"))
            distance += added_dist
            opp_stuff = get_opp_distance_in_schedule(opp, team)
            event = add_dist_and_rest_dict(home, event,distance,team_rest,opp_stuff)
            distance += added_dist
        last_game = event.get("Date")
        output.append(event)
    return output

# Calculates the distance an opponent has traveled up to a certain point
def get_opp_distance_in_schedule(team, stop):
    schedule = get_schedule(team)
    distance = 0
    last_travel = 0
    last_game = ''
    for i in range(len(schedule)):
        event = schedule[i]
        is_neutral_site = bool(event.get("Neutral"))
        if (event.get('Home') == team or event.get('Home') == "FCS") and not is_neutral_site:
            last_travel=0
        elif (event.get('Home') == team and is_neutral_site):
            added_dist = calculate_distance_in_miles(event.get("Home"),event.get("Home"),is_neutral_site,event.get("Lat"),event.get("Lng"))
            last_travel = added_dist
            distance += added_dist*2
        else:
            added_dist = calculate_distance_in_miles(event.get("Away"),event.get("Home"),is_neutral_site,event.get("Lat"),event.get("Lng"))
            last_travel = added_dist
            distance += added_dist*2
        if event.get('Home') == stop or event.get('Away') == stop:
            event.get("Date")
            return [distance-last_travel,get_rest(event,last_game)]
        last_game = event.get("Date")

# Converts date from the espn event format and calculates rest time
def get_rest_time(date1, date2):
    date1 = datetime.strptime(date1, "%Y-%m-%dT%H:%MZ")
    date2 = datetime.strptime(date2, "%Y-%m-%dT%H:%MZ")
    return abs((date1 - date2).days)

# Helper function to access rest_time
def get_rest(event, last_event):
    if last_event == '':
        return 0
    else:
        return get_rest_time(event.get("Date"),last_event)

# Calculates the weight of rest and travel effects
def score_adjustment(dist, opp_dist, rest, opp_rest, is_home):
    if is_home:
        return (opp_dist-dist)/1000 + (rest-opp_rest)/5.5
    else:
        return -((opp_dist-dist)/1000 + (rest-opp_rest)/5.5)

# Extra Data Helper
def add_dist_and_rest_dict(home,event,distance,team_rest,opp_stuff):
    if home:
        event['home_dist'] = round(distance)
        event['home_rest'] = team_rest
        event['away_dist'] = round(opp_stuff[0])
        event['away_rest'] = round(opp_stuff[1])
    else:
        event['home_dist'] = round(opp_stuff[0])
        event['home_rest'] = round(opp_stuff[1])
        event['away_dist'] = round(distance)
        event['away_rest'] = team_rest
    return event

def add_all_games():
    teams = ["Air Force", "Akron", "Alabama", "App State", "Arizona", "Arizona State", "Arkansas", "Arkansas State", "Army", "Auburn", "Ball State", "Baylor", "Boise State", "Boston College", "Bowling Green", "Buffalo", "BYU", "California", "Central Michigan", "Charlotte", "Cincinnati", "Clemson", "Coastal Carolina", "Colorado", "Colorado State", "Duke", "East Carolina", "Eastern Michigan", "Florida", "Florida Atlantic", "Florida International", "Florida State", "Fresno State", "Georgia", "Georgia Southern", "Georgia State", "Georgia Tech", "Hawaii", "Houston", "Illinois", "Indiana", "Iowa", "Iowa State", "Jacksonville State", "James Madison", "Kansas", "Kansas State", "Kennesaw State", "Kent State", "Kentucky", "Liberty", "Louisiana", "Louisiana Tech", "Louisville", "LSU", "Marshall", "Maryland", "Massachusetts", "Memphis", "Miami", "Miami (OH)", "Michigan", "Michigan State", "Middle Tennessee", "Minnesota", "Mississippi State", "Missouri", "Navy", "NC State", "Nebraska", "Nevada", "New Mexico", "New Mexico State", "North Carolina", "Northern Illinois", "North Texas", "Northwestern", "Notre Dame", "Ohio", "Ohio State", "Oklahoma", "Oklahoma State", "Old Dominion", "Ole Miss", "Oregon", "Oregon State", "Penn State", "Pittsburgh", "Purdue", "Rice", "Rutgers", "Sam Houston", "San Diego State", "San José State", "SMU", "South Alabama", "South Carolina", "Southern Miss", "South Florida", "Stanford", "Syracuse", "TCU", "Temple", "Tennessee", "Texas", "Texas A&M", "Texas State", "Texas Tech", "Toledo", "Troy", "Tulane", "Tulsa", "UAB", "UCF", "UCLA", "UConn", "UL Monroe", "UNLV", "USC", "Utah", "Utah State", "UTEP", "UTSA", "Vanderbilt", "Virginia", "Virginia Tech", "Wake Forest", "Washington", "Washington State", "Western Kentucky", "Western Michigan", "West Virginia", "Wisconsin", "Wyoming", "Delaware", "Missouri State"]
    for i in teams:
        for j in get_game_information(i):
            database_query.insert_game_info(j)
        print("Completed: " + i)

for i in database_query.get_team_schedule_info("Alabama"):
    print(i)

