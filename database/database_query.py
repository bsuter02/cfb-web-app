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