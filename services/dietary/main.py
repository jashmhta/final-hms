"""
main module
"""

from datetime import datetime
from typing import List, Optional

import crud
import models
import schemas
from database import Base, engine, get_db
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Dietary Service",
    description="Enterprise-grade dietary management for hospitals",
    version="1.0.0",
)


@app.get("/")
async def root():
    return {"message": "Dietary Service is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.post("/patient-requirements/", response_model=schemas.PatientDietRequirement)
def create_patient_diet_requirement(
    requirement: schemas.PatientDietRequirementCreate, db: Session = Depends(get_db)
):
    return crud.create_patient_diet_requirement(db, requirement)


@app.get(
    "/patient-requirements/{patient_id}", response_model=schemas.PatientDietRequirement
)
def read_patient_diet_requirement(patient_id: str, db: Session = Depends(get_db)):
    requirement = crud.get_patient_diet_requirement(db, patient_id)
    if requirement is None:
        raise HTTPException(
            status_code=404, detail="Patient diet requirement not found"
        )
    return requirement


@app.put(
    "/patient-requirements/{patient_id}", response_model=schemas.PatientDietRequirement
)
def update_patient_diet_requirement(
    patient_id: str,
    requirement: schemas.PatientDietRequirementCreate,
    db: Session = Depends(get_db),
):
    return crud.update_patient_diet_requirement(db, patient_id, requirement)


@app.post("/food-items/", response_model=schemas.FoodItem)
def create_food_item(food_item: schemas.FoodItemCreate, db: Session = Depends(get_db)):
    return crud.create_food_item(db, food_item)


@app.get("/food-items/", response_model=List[schemas.FoodItem])
def read_food_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_food_items(db, skip=skip, limit=limit)


@app.get("/food-items/{food_id}", response_model=schemas.FoodItem)
def read_food_item(food_id: str, db: Session = Depends(get_db)):
    food_item = crud.get_food_item(db, food_id)
    if food_item is None:
        raise HTTPException(status_code=404, detail="Food item not found")
    return food_item


@app.get("/food-items/search/{query}", response_model=List[schemas.FoodItem])
def search_food_items(query: str, db: Session = Depends(get_db)):
    return crud.search_food_items(db, query)


@app.post("/meal-plans/", response_model=schemas.MealPlan)
def create_meal_plan(meal_plan: schemas.MealPlanCreate, db: Session = Depends(get_db)):
    return crud.create_meal_plan(db, meal_plan)


@app.get("/meal-plans/", response_model=List[schemas.MealPlan])
def read_meal_plans(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_meal_plans(db, skip=skip, limit=limit)


@app.get("/meal-plans/{plan_id}", response_model=schemas.MealPlan)
def read_meal_plan(plan_id: str, db: Session = Depends(get_db)):
    meal_plan = crud.get_meal_plan(db, plan_id)
    if meal_plan is None:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return meal_plan


@app.get("/meal-plans/patient/{patient_id}", response_model=List[schemas.MealPlan])
def read_patient_meal_plans(patient_id: str, db: Session = Depends(get_db)):
    return crud.get_patient_meal_plans(db, patient_id)


@app.post("/meals/", response_model=schemas.Meal)
def create_meal(meal: schemas.MealCreate, db: Session = Depends(get_db)):
    return crud.create_meal(db, meal)


@app.get("/meals/", response_model=List[schemas.Meal])
def read_meals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_meals(db, skip=skip, limit=limit)


@app.get("/meals/{meal_id}", response_model=schemas.Meal)
def read_meal(meal_id: str, db: Session = Depends(get_db)):
    meal = crud.get_meal(db, meal_id)
    if meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    return meal


@app.get("/meals/date/{date}", response_model=List[schemas.Meal])
def read_meals_by_date(date: str, db: Session = Depends(get_db)):
    try:
        meal_date = datetime.fromisoformat(date).date()
        return crud.get_meals_by_date(db, meal_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")


@app.patch("/meals/{meal_id}/serve")
def update_meal_status(meal_id: str, served: bool, db: Session = Depends(get_db)):
    return crud.update_meal_status(db, meal_id, served)


@app.post("/meal-items/", response_model=schemas.MealItem)
def create_meal_item(meal_item: schemas.MealItemCreate, db: Session = Depends(get_db)):
    return crud.create_meal_item(db, meal_item)


@app.get("/meal-items/meal/{meal_id}", response_model=List[schemas.MealItem])
def read_meal_items(meal_id: int, db: Session = Depends(get_db)):
    return crud.get_meal_items(db, meal_id)


@app.post("/menus/", response_model=schemas.Menu)
def create_menu(menu: schemas.MenuCreate, db: Session = Depends(get_db)):
    return crud.create_menu(db, menu)


@app.get("/menus/", response_model=List[schemas.Menu])
def read_menus(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_menus(db, skip=skip, limit=limit)


@app.get("/menus/{menu_id}", response_model=schemas.Menu)
def read_menu(menu_id: str, db: Session = Depends(get_db)):
    menu = crud.get_menu(db, menu_id)
    if menu is None:
        raise HTTPException(status_code=404, detail="Menu not found")
    return menu


@app.get("/menus/diet/{diet_type}", response_model=List[schemas.Menu])
def read_menus_by_diet_type(diet_type: schemas.DietType, db: Session = Depends(get_db)):
    return crud.get_menus_by_diet_type(db, diet_type)


@app.post("/menu-items/", response_model=schemas.MenuItem)
def create_menu_item(menu_item: schemas.MenuItemCreate, db: Session = Depends(get_db)):
    return crud.create_menu_item(db, menu_item)


@app.get("/menu-items/menu/{menu_id}", response_model=List[schemas.MenuItem])
def read_menu_items(menu_id: int, db: Session = Depends(get_db)):
    return crud.get_menu_items(db, menu_id)


@app.post("/nutrition-calculations/", response_model=schemas.NutritionCalculation)
def create_nutrition_calculation(
    calculation: schemas.NutritionCalculationCreate, db: Session = Depends(get_db)
):
    return crud.create_nutrition_calculation(db, calculation)


@app.get(
    "/nutrition-calculations/{patient_id}", response_model=schemas.NutritionCalculation
)
def read_nutrition_calculation(patient_id: str, db: Session = Depends(get_db)):
    calculation = crud.get_nutrition_calculation(db, patient_id)
    if calculation is None:
        raise HTTPException(status_code=404, detail="Nutrition calculation not found")
    return calculation


@app.put(
    "/nutrition-calculations/{patient_id}", response_model=schemas.NutritionCalculation
)
def update_nutrition_calculation(
    patient_id: str,
    calculation: schemas.NutritionCalculationCreate,
    db: Session = Depends(get_db),
):
    return crud.update_nutrition_calculation(db, patient_id, calculation)


@app.get("/statistics", response_model=schemas.DietaryStatistics)
def get_dietary_statistics(db: Session = Depends(get_db)):
    return crud.get_dietary_statistics(db)


@app.get("/dashboard", response_model=schemas.DietaryDashboard)
def get_dietary_dashboard(db: Session = Depends(get_db)):
    return crud.get_dietary_dashboard(db)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9010)
