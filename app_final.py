import os
import sqlite3
from datetime import date, datetime
from typing import List, Literal

import streamlit as st
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field


load_dotenv()

DB_PATH = "diet_tracker.db"


# ============================================================
# AI RESPONSE MODEL
# ============================================================

class MealAnalysis(BaseModel):
    total_calories: float = Field(
        description="Estimated total calories"
    )
    total_protein_g: float = Field(
        description="Estimated protein in grams"
    )
    total_carbs_g: float = Field(
        description="Estimated carbohydrates in grams"
    )
    total_fat_g: float = Field(
        description="Estimated fat in grams"
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Assumptions made about serving sizes or ingredients"
    )
    confidence: Literal["low", "medium", "high"] = Field(
        description="Confidence level of the estimate"
    )


# ============================================================
# AI MEAL ANALYSIS
# ============================================================

@st.cache_resource
def get_meal_chain():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return None

    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
        api_key=api_key,
    )

    structured_llm = llm.with_structured_output(MealAnalysis)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are a nutrition tracking assistant.

Estimate nutrition for the complete meal description.

Use average serving sizes when the user does not provide amounts.

Clearly list your assumptions.

Return total nutrition values for the entire meal.

Do not provide medical advice or claim certainty.
""",
            ),
            (
                "user",
                "{meal_description}",
            ),
        ]
    )

    return prompt | structured_llm


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS food_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eaten_date TEXT NOT NULL,
            meal_type TEXT NOT NULL,
            description TEXT NOT NULL,
            calories REAL NOT NULL,
            protein_g REAL NOT NULL,
            carbs_g REAL NOT NULL,
            fat_g REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


def save_meal(
    eaten_date,
    meal_type,
    description,
    calories,
    protein_g,
    carbs_g,
    fat_g,
):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO food_entries (
            eaten_date,
            meal_type,
            description,
            calories,
            protein_g,
            carbs_g,
            fat_g,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            eaten_date,
            meal_type,
            description,
            calories,
            protein_g,
            carbs_g,
            fat_g,
            datetime.now().isoformat(),
        ),
    )

    connection.commit()
    connection.close()


def get_daily_entries(selected_date):
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            meal_type,
            description,
            calories,
            protein_g,
            carbs_g,
            fat_g
        FROM food_entries
        WHERE eaten_date = ?
        ORDER BY created_at DESC
        """,
        (selected_date,),
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


# ============================================================
# SESSION STATE
# ============================================================

def initialize_session_state():
    defaults = {
        "meal_description": "",
        "calories": 0.0,
        "protein": 0.0,
        "carbs": 0.0,
        "fat": 0.0,
        "assumptions": [],
        "confidence": "",
        "save_success": False,
        "save_error": None,
        "clear_meal": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_meal_state():
    """
    This function must only be called BEFORE widgets using
    these keys are instantiated.
    """
    st.session_state["meal_description"] = ""
    st.session_state["calories"] = 0.0
    st.session_state["protein"] = 0.0
    st.session_state["carbs"] = 0.0
    st.session_state["fat"] = 0.0
    st.session_state["assumptions"] = []
    st.session_state["confidence"] = ""


# ============================================================
# SAVE CALLBACK
# ============================================================

def save_current_meal(eaten_date, meal_type):
    description = st.session_state.get(
        "meal_description",
        ""
    ).strip()

    if not description:
        st.session_state["save_error"] = (
            "Please describe what you ate."
        )
        st.session_state["save_success"] = False
        return

    try:
        save_meal(
            eaten_date,
            meal_type,
            description,
            st.session_state.get("calories", 0.0),
            st.session_state.get("protein", 0.0),
            st.session_state.get("carbs", 0.0),
            st.session_state.get("fat", 0.0),
        )

        # IMPORTANT:
        # Do not modify widget state here.
        # Set a flag so it is cleared at the beginning
        # of the next Streamlit rerun.
        st.session_state["save_success"] = True
        st.session_state["save_error"] = None
        st.session_state["clear_meal"] = True

    except Exception as error:
        st.session_state["save_success"] = False
        st.session_state["save_error"] = str(error)


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():

    st.set_page_config(
        page_title="Diet Tracker",
        page_icon="🥗",
        layout="wide",
    )

    initialize_database()
    initialize_session_state()

    # ========================================================
    # IMPORTANT:
    # Clear widget state BEFORE creating the widgets.
    # This prevents:
    #
    # StreamlitAPIException:
    # "st.session_state.xxx cannot be modified after
    # the widget with key xxx is instantiated."
    # ========================================================

    if st.session_state["clear_meal"]:
        clear_meal_state()
        st.session_state["clear_meal"] = False

    # ========================================================
    # HEADER
    # ========================================================

    st.title("🥗 Diet Tracker")
    st.write(
        "Log your meals and track your daily nutrition."
    )

    # ========================================================
    # SIDEBAR GOALS
    # ========================================================

    st.sidebar.header("Daily Goals")

    calorie_goal = st.sidebar.number_input(
        "Calories",
        min_value=0,
        value=2200,
        step=50,
    )

    protein_goal = st.sidebar.number_input(
        "Protein (g)",
        min_value=0,
        value=150,
        step=5,
    )

    carbs_goal = st.sidebar.number_input(
        "Carbohydrates (g)",
        min_value=0,
        value=250,
        step=5,
    )

    fat_goal = st.sidebar.number_input(
        "Fat (g)",
        min_value=0,
        value=70,
        step=5,
    )

    # ========================================================
    # MEAL INPUT
    # ========================================================

    st.header("Log a meal")

    meal_date = st.date_input(
        "Date",
        value=date.today(),
    )

    meal_type = st.selectbox(
        "Meal type",
        [
            "Breakfast",
            "Lunch",
            "Dinner",
            "Snack",
        ],
    )

    st.text_input(
        "What did you eat?",
        placeholder=(
            "Example: I had 2 eggs, toast, and a banana"
        ),
        key="meal_description",
    )

    # ========================================================
    # AI ANALYSIS
    # ========================================================

    if st.button("Analyze with AI"):

        if not st.session_state["meal_description"].strip():

            st.error(
                "Please describe what you ate."
            )

        else:

            meal_chain = get_meal_chain()

            if meal_chain is None:

                st.error(
                    "GROQ_API_KEY was not found. "
                    "Add it to your .env file and restart "
                    "the app."
                )

            else:

                try:

                    with st.spinner(
                        "Analyzing your meal..."
                    ):

                        result = meal_chain.invoke(
                            {
                                "meal_description":
                                    st.session_state[
                                        "meal_description"
                                    ]
                            }
                        )

                    st.session_state["calories"] = float(
                        result.total_calories
                    )

                    st.session_state["protein"] = float(
                        result.total_protein_g
                    )

                    st.session_state["carbs"] = float(
                        result.total_carbs_g
                    )

                    st.session_state["fat"] = float(
                        result.total_fat_g
                    )

                    st.session_state["assumptions"] = (
                        result.assumptions
                    )

                    st.session_state["confidence"] = (
                        result.confidence
                    )

                    st.success(
                        "Meal analyzed. Review the values "
                        "before saving."
                    )

                except Exception as error:

                    st.error(
                        f"AI analysis failed: {error}"
                    )

    # ========================================================
    # NUTRITION VALUES
    # ========================================================

    st.subheader("Nutrition values")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.number_input(
            "Calories",
            min_value=0.0,
            step=10.0,
            key="calories",
        )

    with col2:

        st.number_input(
            "Protein (g)",
            min_value=0.0,
            step=1.0,
            key="protein",
        )

    with col3:

        st.number_input(
            "Carbs (g)",
            min_value=0.0,
            step=1.0,
            key="carbs",
        )

    with col4:

        st.number_input(
            "Fat (g)",
            min_value=0.0,
            step=1.0,
            key="fat",
        )

    # ========================================================
    # AI INFORMATION
    # ========================================================

    if st.session_state["confidence"]:

        st.caption(
            "AI confidence: "
            + st.session_state["confidence"]
        )

    if st.session_state["assumptions"]:

        st.info(
            "Assumptions: "
            + "; ".join(
                st.session_state["assumptions"]
            )
        )

    # ========================================================
    # SAVE MEAL
    # ========================================================

    st.button(
        "Save meal",
        on_click=save_current_meal,
        args=(
            meal_date.isoformat(),
            meal_type,
        ),
    )

    # ========================================================
    # SAVE STATUS
    # ========================================================

    if st.session_state.get("save_success"):

        st.success(
            "Meal saved successfully."
        )

        # Only reset the status flag.
        # Actual widget clearing happens at the beginning
        # of the next rerun.
        st.session_state["save_success"] = False

    if st.session_state.get("save_error"):

        st.error(
            st.session_state["save_error"]
        )

        st.session_state["save_error"] = None

    # ========================================================
    # DAILY MEALS
    # ========================================================

    st.subheader("Today's meals")

    selected_date = meal_date.isoformat()

    entries = get_daily_entries(
        selected_date
    )

    if not entries:

        st.info(
            "No meals logged for this date."
        )

    else:

        total_calories = sum(
            entry["calories"]
            for entry in entries
        )

        total_protein = sum(
            entry["protein_g"]
            for entry in entries
        )

        total_carbs = sum(
            entry["carbs_g"]
            for entry in entries
        )

        total_fat = sum(
            entry["fat_g"]
            for entry in entries
        )

        metric1, metric2, metric3, metric4 = (
            st.columns(4)
        )

        metric1.metric(
            "Calories",
            f"{total_calories:.0f} / "
            f"{calorie_goal:.0f} kcal",
        )

        metric2.metric(
            "Protein",
            f"{total_protein:.1f} / "
            f"{protein_goal:.0f} g",
        )

        metric3.metric(
            "Carbs",
            f"{total_carbs:.1f} / "
            f"{carbs_goal:.0f} g",
        )

        metric4.metric(
            "Fat",
            f"{total_fat:.1f} / "
            f"{fat_goal:.0f} g",
        )

        st.dataframe(
            entries,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
