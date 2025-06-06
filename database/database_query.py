import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("HOST")
DB_USER = os.getenv("USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DATABASE = os.getenv("DATABASE")

# Creates the connection to the MySQL Database
def get_connection():
    connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
    return connection

def get_cfb_fpi_by_team(team):
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = "SELECT * FROM CfbPowerRating WHERE TeamName = %s;"
        cursor.execute(query, (team,))

        results = cursor.fetchone()

        return results  # Returns a dict with each field in the fpi table

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_cfb_hfa_by_team(team):
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = "SELECT * FROM HFA WHERE TeamName = %s;"
        cursor.execute(query, (team,))

        results = cursor.fetchone()

        return results  # Returns a dict with each field in the hfa table

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_cfb_sp_plus_by_team(team):
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = "SELECT * FROM CfbSPPlusRating WHERE TeamName = %s;"
        cursor.execute(query, (team,))

        results = cursor.fetchone()

        return results  # Returns a dict with each field in the fpi table

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_teamname_by_nickname(team):
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = "SELECT TeamName FROM ESPN_ID WHERE ESPN_Nickname = %s;"
        cursor.execute(query, (team,))

        results = cursor.fetchone()

        return results  # Returns a dict with each field in the fpi table

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_id_by_teamname(team):
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = "SELECT ESPN_ID FROM ESPN_ID WHERE TeamName = %s;"
        cursor.execute(query, (team,))

        results = cursor.fetchone()

        return results  # Returns a dict with each field in the fpi table

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def insert_game_info(game_info):
    game = {
        "ID":int(game_info.get('ID')),
        "AwayName":game_info.get('Away'),
        "HomeName":game_info.get('Home'),
        "NeutralSite":bool(game_info.get('Neutral')),
        "WeekNumber":int(game_info.get('Week')),
        "HomeDist":game_info.get('home_dist'),
        "AwayDist":game_info.get('away_dist'),
        "HomeRest":game_info.get('home_rest'),
        "AwayRest":game_info.get('away_rest'),
        "HomeScore":-1,
        "AwayScore":-1
    }
    insert_data = ("INSERT INTO GameInfo "
            "(ID, AwayName, HomeName, NeutralSite, WeekNumber, HomeDist, AwayDist, HomeRest, AwayRest, HomeScore, AwayScore) "
            "VALUES (%(ID)s, %(AwayName)s, %(HomeName)s, %(NeutralSite)s, %(WeekNumber)s, %(HomeDist)s, %(AwayDist)s, %(HomeRest)s, %(AwayRest)s, %(HomeScore)s, %(AwayScore)s)"
            "ON DUPLICATE KEY UPDATE "
            "HomeScore = VALUES(HomeScore), "
            "AwayScore = VALUES(AwayScore);")

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(insert_data, game)

        connection.commit()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()