from pydantic import BaseModel
from datetime import date

class Meal(BaseModel):
    id: int | None = None
    date: date
    meal_type: str
    description: str
    calories: float
    protein: float
    carbs: float
    fat: float