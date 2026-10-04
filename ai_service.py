
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from Model.Meal import Meal

llm = ChatGroq(model="openai/gpt-oss-120b", streaming=True)

structured_llm = llm.with_structured_output(Meal)

def analyze_food(meal_description: str) -> Meal:
    """
    Analyze the meal description and return structured meal data.

    Args:
        meal_description (str): Description of the meal.

    Returns:
        MealOutput: Structured meal data including meal type, items, total nutrients, assumptions, and confidence.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a nutrition expert. Analyze the meal description and provide structured meal data."),
        ("user", "Analyze the following meal description: {meal_description}")
    ])

    chain = prompt | structured_llm

    result = chain.invoke({"meal_description": meal_description})

    return result