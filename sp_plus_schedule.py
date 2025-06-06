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

# Get the score adjustment from travel and rest effects for a whole schedule 
def schedule_predictor_sp_plus(team):
    schedule = get_schedule(team)
    distance = 0
    last_game = ''
    for i in range(len(schedule)):
        event = schedule[i]
        is_neutral_site = bool(event.get("Neutral"))
        # Determines who the opponent is
        opp = event.get("Home")
        if(opp == team):
            opp = event.get("Away")
        # Excludes distance traveled by FCS teams and home games from distance calculation
        if (event.get('Home') == team or event.get('Home') == "FCS") and not is_neutral_site:
            if(event.get('Away') == "FCS"):
                print(event.get("Away") + ": 7; " + event.get("Home") + ": 49")
            else:
                opp_stuff = get_opp_distance_in_schedule(opp, team)
                print(predict_schedule_sp_plus(event.get("Away"),event.get("Home"),score_adjustment(distance, opp_stuff[0],get_rest(event, last_game),opp_stuff[1],True)))
        # Calculates Neutral site distance traveled
        elif (event.get('Home') == team and is_neutral_site):
            added_dist = calculate_distance_in_miles(event.get("Home"),event.get("Home"),is_neutral_site,event.get("Lat"),event.get("Lng"))
            distance += added_dist
            opp_stuff = get_opp_distance_in_schedule(opp, team)
            print(predict_schedule_sp_plus(event.get("Away"),event.get("Home"),score_adjustment(distance, opp_stuff[0],get_rest(event, last_game),opp_stuff[1],True)))
            distance += added_dist
        # Calculates standard away distance traveled
        else:
            added_dist = calculate_distance_in_miles(event.get("Away"),event.get("Home"),is_neutral_site,event.get("Lat"),event.get("Lng"))
            distance += added_dist
            opp_stuff = get_opp_distance_in_schedule(opp, team)
            print(predict_schedule_sp_plus(event.get("Away"),event.get("Home"),score_adjustment(distance, opp_stuff[0],get_rest(event, last_game),opp_stuff[1],False)))
            distance += added_dist
        last_game = event.get("Date")

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

# Predicts the score of a game using SP+, weighted for travel and rest
def predict_schedule_sp_plus(away, home, adjustment):
    
    # Pull FPI, Offensive Efficiency, and Defensive Efficiency for each team as determined by ESPN analytics.
    away_team = database_query.get_cfb_sp_plus_by_team(away)
    home_team = database_query.get_cfb_sp_plus_by_team(home)

    # Grabs Home Field Advantage for the team hosting, as determined in an online analysis.
    home_hfa = database_query.get_cfb_hfa_by_team(home)
    
    # Estimates how much of the total score each team is responsible for, not used at the score prediction as the margin provided by sp+ accomplishes this.
    home_factor = ((float(home_team.get("OffPoint"))) + (float(away_team.get("DefPoint"))))/2
    away_factor = ((float(away_team.get("OffPoint"))) + (float(home_team.get("DefPoint"))))/2

    # Estimates total score.
    total_score = home_factor + away_factor

    # Estimates margin of victory without accounting for home field advantage, impact of travel, or rest time prior to the game.
    raw_margin = float(home_team.get("SPPlus")) - float(away_team.get("SPPlus"))

    # Estimates the score accounting HFA.
    away_score = boundary_adjustments(total_score/2 - raw_margin/2 - float(home_hfa.get("HFA"))/2 - adjustment/2)
    home_score = boundary_adjustments(total_score/2 + raw_margin/2 + float(home_hfa.get("HFA"))/2 + adjustment/2)

    # Accounts for ties at end of regulation (doesn't do OT, determines the non-rounded advantage if any, defaults to hfa if exact tie)
    home_score, away_score = tie_breaker(home_score,away_score,float(home_team.get("SPPlus")),float(away_team.get("SPPlus")),float(home_hfa.get("HFA")))
    
    return away_team.get("TeamName") + ": " + str(round(away_score)) + "; " + home_team.get("TeamName") + ": " + str(round(home_score))

# Some results have unrealistically low scores
def boundary_adjustments(score):
    if score < 0:
        score = 0
    elif score < 3:
        score = 3
    elif score < 6:
        score = 6
    return score

# Adds a point if the rounded score is tied, favors home team if non rounded results are tied too.
def tie_breaker(score1, score2, home_sp, away_sp, hfa):
    score = max(score1,score2)
    if abs(score1-score2) > 0.5 and (round(score1) == round(score2)): # Assumes margin great enough for a 1 point win in regulation
        if score1 > score2:
            score1 = score1 + 1
            score2 = score2
        else:
            score1 = score1
            score2 = score2 + 1

    elif abs(score1-score2) <= 0.5: # Assume margin small enough for overtime. Assume FG to win, may adjust based on offense v defense of winning team if it's a TD or not.
        if (away_sp-home_sp)<hfa:
            score1 = score + 3
            score2 = score
        else:
            score1 = score
            score2 = score + 3
    return round(score1), round(score2)

# Calculates a game's score using data from locally stored db
def sp_score(game):
    # Pull FPI, Offensive Efficiency, and Defensive Efficiency for each team as determined by ESPN analytics.
    away_team = str(game.get("AwayName"))
    home_team = str(game.get("HomeName"))

    if away_team == "FCS":
        away_team = {'TeamName': 'FCS', 'SPPlus': float(-31.81), 'OffPoint': float(11.92), 'DefPoint': float(43.73)}
        home_team = dict(database_query.get_cfb_sp_plus_by_team(home_team))
    elif home_team == "FCS":
        home_team = {'TeamName': 'FCS', 'SPPlus': float(-31.81), 'OffPoint': float(11.92), 'DefPoint': float(43.73)}
        away_team = dict(database_query.get_cfb_sp_plus_by_team(away_team))
    else:
        away_team = dict(database_query.get_cfb_sp_plus_by_team(away_team))
        home_team = dict(database_query.get_cfb_sp_plus_by_team(home_team))

    #print(away_team)
    #print(home_team)

    # Grabs Home Field Advantage for the team hosting, as determined in an online analysis.
    home_hfa = database_query.get_cfb_hfa_by_team(home_team.get("TeamName"))
    
    # Estimates how much of the total score each team is responsible for, not used at the score prediction as the margin provided by sp+ accomplishes this.
    home_factor = ((float(home_team.get("OffPoint"))) + (float(away_team.get("DefPoint"))))/2
    away_factor = ((float(away_team.get("OffPoint"))) + (float(home_team.get("DefPoint"))))/2

    # Estimates total score.
    total_score = home_factor + away_factor

    # Estimates margin of victory without accounting for home field advantage, impact of travel, or rest time prior to the game.
    raw_margin = float(home_team.get("SPPlus")) - float(away_team.get("SPPlus"))

    # Calculates impact of travel and rest time
    adjustment = (int(game.get("HomeRest"))-int(game.get("AwayRest")))/5.5 + (int(game.get("AwayDist"))-int(game.get("HomeDist")))/1000

    # Estimates the score accounting HFA.
    away_score = boundary_adjustments(total_score/2 - raw_margin/2 - float(home_hfa.get("HFA"))/2 - adjustment/2)
    home_score = boundary_adjustments(total_score/2 + raw_margin/2 + float(home_hfa.get("HFA"))/2 + adjustment/2)

    # Accounts for ties at end of regulation (doesn't do OT, determines the non-rounded advantage if any, defaults to hfa if exact tie)
    home_score, away_score = tie_breaker(home_score,away_score,float(home_team.get("SPPlus")),float(away_team.get("SPPlus")),float(home_hfa.get("HFA")))
    
    return away_team.get("TeamName") + ": " + str(round(away_score)) + "; " + home_team.get("TeamName") + ": " + str(round(home_score))

# Returns the score prediction for the next fooball year (as of 6/5/25, this is the 2025 schedule)
def db_sp_plus_schedule(team):
    games = database_query.get_team_schedule_info(team)
    for i in games:
        print(sp_score(i))

db_sp_plus_schedule("Ohio State")