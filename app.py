import streamlit as st
from Model.Meal import Meal
from ai_service import analyze_food 
import database
import pandas as pd
from datetime import date

st.set_page_config(page_title="Diet Tracker App", page_icon=":apple:", layout="wide")

st.title("Diet Tracker App 🥗")

st.subheader("Track your meals and nutrition effortlessly!")

def main():

    def reset_form():
        st.session_state.meal_date = date.today()
        st.session_state.meal_type = "Select meal type"
        st.session_state.meal_description = ""
        st.session_state.calories = 0.0
        st.session_state.protein = 0.0
        st.session_state.carbs = 0.0
        st.session_state.fat = 0.0

    meals = database.get_meals(database.create_connection())

    if st.session_state.get("load_edit_meal", False):
        edit_meal_id = st.session_state.get("edit_meal_id", None)

        for meal in meals:
            if meal.id == st.session_state["edit_meal_id"]:
                st.session_state["meal_date"] = meal.date
                st.session_state["meal_type"] = meal.meal_type
                st.session_state["meal_description"] = meal.description
                st.session_state["calories"] = meal.calories
                st.session_state["protein"] = meal.protein
                st.session_state["carbs"] = meal.carbs
                st.session_state["fat"] = meal.fat
                break

        st.session_state["load_edit_meal"] = False

    with st.form("meal_form", clear_on_submit=False):
        st.date_input("Date of Meal", key="meal_date")
        st.selectbox("Meal Type", ["Select meal of the day","Breakfast", "Lunch", "Dinner", "Snack"], key="meal_type")
        st.text_area("Meal Description", placeholder="Describe your meal...", key="meal_description")
        get_calories = st.form_submit_button("Get Calories") 

        if get_calories:
            meal_description = st.session_state.meal_description
            result = analyze_food(meal_description)            
            
            st.session_state['calories'] = result.calories
            st.session_state['protein'] = result.protein
            st.session_state['carbs'] = result.carbs
            st.session_state['fat'] = result.fat        

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.number_input("Calories", key="calories", step=5.0)
    with col2:
        st.number_input("Protein", key="protein", step=1.0)
    with col3:
        st.number_input("Carbs", key="carbs", step=1.0)
    with col4:
        st.number_input("Fat", key="fat", step=1.0)

    meal = Meal(
        date=st.session_state.meal_date,
        meal_type=st.session_state.meal_type,
        description=st.session_state.meal_description,
        calories=st.session_state.calories,
        protein=st.session_state.protein,
        carbs=st.session_state.carbs,
        fat=st.session_state.fat
    )
    # st.session_state['meal'] = meal

    def save_meal():
        meal = Meal(
            id=st.session_state.get("edit_meal_id", None),
            date=st.session_state.meal_date,
            meal_type=st.session_state.meal_type,
            description=st.session_state.meal_description,
            calories=st.session_state.calories,
            protein=st.session_state.protein,
            carbs=st.session_state.carbs,
            fat=st.session_state.fat
        )

        conn = database.create_connection()
        if conn:
            if meal.id is not None:
                database.update_meal(conn, meal)
                st.success("Meal updated successfully!")
                st.session_state["edit_meal_id"] = None
                reset_form()
            else:
                database.insert_meal(conn, meal)
                st.success("Meal saved successfully!")
                reset_form()
        else:
            st.error("Failed to connect to the database.")

    st.button("Save Meal", on_click=save_meal)

    meal_dicts = [meal.model_dump() for meal in meals]

    df = pd.DataFrame(
    meal_dicts,
    columns=["id", "date", "meal_type", "description", "calories", "protein", "carbs", "fat"]
)

    df["date"] = pd.to_datetime(df["date"]).dt.date

    selected_date = st.date_input(
        "Select Date to View Meals",
        value=date.today()
    )

    selected_date_meals = df[df["date"] == selected_date]

    total_calories = round(selected_date_meals["calories"].sum(), 1)
    total_protein = round(selected_date_meals["protein"].sum(), 1)
    total_carbs = round(selected_date_meals["carbs"].sum(), 1)
    total_fat = round(selected_date_meals["fat"].sum(), 1)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Calories", total_calories)
    with col2:
        st.metric("Total Protein", total_protein)
    with col3:
        st.metric("Total Carbs", total_carbs)
    with col4:
        st.metric("Total Fat", total_fat)
    
    if not selected_date_meals.empty:
        st.subheader("Saved Meals")

    ## column headers
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 2, 1, 1, 1, 1, 1, 1]    )

    with col1:
        st.write("Meal Type")
    with col2:
        st.write("Description")
    with col3:
        st.write("Calories")
    with col4:
        st.write("Protein")
    with col5:
        st.write("Carbs")
    with col6:
        st.write("Fat")
    with col7:
        st.write("Action")
    with col8:
        st.write("Action")

    st.markdown("---")

    for row in selected_date_meals.itertuples():
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 2, 1, 1, 1, 1, 1, 1])
        with col1:
            st.write(row.meal_type)
        with col2:
            st.write(row.description)
        with col3:
            st.write(row.calories)
        with col4:
            st.write(row.protein)
        with col5:
            st.write(row.carbs)
        with col6:
            st.write(row.fat)
        with col7:
            if st.button("Update", key=f"edit_{row.id}"):
                st.session_state["edit_meal_id"] = row.id
                st.session_state["load_edit_meal"] = True
                st.rerun()
        with col8:
            if st.button("Delete", key=f"delete_{row.id}"):
                conn = database.create_connection()
                if conn:
                    database.delete_meal(conn, row.id)
                    st.success("Meal deleted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to connect to the database.")
        st.markdown("---")

if __name__ == "__main__":
    main()