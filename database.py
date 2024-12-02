import mysql.connector
from mysql.connector import Error

class Database:
    def __init__(self):
        try:
            self.connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="face_attendance",
                charset='utf8mb4'
            )
            if self.connection.is_connected():
                print("Database connection successful!")
        except Error as e:
            print(f"Error: {str(e)}")

    def execute_query(self, query, params=None):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            self.connection.commit()
            return cursor
        except Error as e:
            print(f"Query execution error: {str(e)}")
            return None
        finally:
            cursor.close()

    def fetch_data(self, query, params=None):
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            print(f"Data fetch error: {str(e)}")
            return None
        finally:
            cursor.close()