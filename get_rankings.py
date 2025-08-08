import requests

from database.database_query import get_team_name_from_espn_id

rankList = []

# Retrieves and prints the AP top 25 from ESPN
def get_ap_top_25():
    global rankList
    rankList = []
    url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/rankings"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        ap_rankings = None
        for ranking in data.get("rankings", []):
            if ranking.get("type") == "ap":
                ap_rankings = ranking.get("ranks", [])
                break
        if ap_rankings:
            for rank, team in enumerate(ap_rankings, start=1):
                #print(f"Team dictionary for rank {rank}: {team}")
                team_name = team.get("team", {}).get("nickname", "Unknown Team")
                team_abbr = team.get("team", {}).get("id", "Unknown Team") # Switch to abbreviation to id
                record = "(" + team.get("recordSummary", "N/A") + ")"
                color = "#" + team.get("team", {}).get("color", "cc0000")
                name = get_team_name_from_espn_id(int(team_abbr))
                png_name = ''.join(name.split())
                rankList.append({"abbr": png_name.upper() + ".png", "name": team_name.upper(), "record": record, "color": color})
                #print(f"{rank}. {team_name} ({record}) {color}")
            return rankList
        else:
            print("AP Top 25 rankings not found.")
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")

rankList2 = get_ap_top_25()
for i in range(len(rankList2)):
    print(rankList2[i])