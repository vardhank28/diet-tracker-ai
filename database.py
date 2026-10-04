import sqlite3
from  Model.Meal import Meal

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect("diet_tracker.db")
        print("Connected to database: diet_tracker.db")
        create_table(conn)
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_table(conn):
    conn.execute("""
    CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        meal_type TEXT NOT NULL,
        description TEXT,
        calories REAL NOT NULL,
        protein REAL NOT NULL,
        carbs REAL NOT NULL,
        fat REAL NOT NULL
    );
    """)
    conn.commit()

def insert_meal(conn, meal):
    conn.execute("""
    INSERT INTO meals (id,date, meal_type, description, calories, protein, carbs, fat)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (meal.id, meal.date, meal.meal_type, meal.description, meal.calories, meal.protein, meal.carbs, meal.fat))
    conn.commit()

def get_meals(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals;")
    rows = cursor.fetchall()

    meals = []

    for row in rows:
        meal = Meal(
            id=row[0],
            date=row[1],
            meal_type=row[2],
            description=row[3],
            calories=row[4],
            protein=row[5],
            carbs=row[6],
            fat=row[7]
        )
        meals.append(meal)

    return meals


def update_meal(conn, meal):
    conn.execute("""
    UPDATE meals
    SET date = ?, meal_type = ?, description = ?, calories = ?, protein = ?, carbs = ?, fat = ?
    WHERE id = ?;
    """, (meal.date, meal.meal_type, meal.description, meal.calories, meal.protein, meal.carbs, meal.fat, meal.id))
    conn.commit()

def delete_meal(conn, meal_id):
    conn.execute("DELETE FROM meals WHERE id = ?;", (meal_id,))
    conn.commit()


   