from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
import models
import schemas
def get_patient_diet_requirement(db: Session, patient_id: str):
    return db.query(models.PatientDietRequirement).filter(models.PatientDietRequirement.patient_id == patient_id).first()
def create_patient_diet_requirement(db: Session, requirement: schemas.PatientDietRequirementCreate):
    db_requirement = models.PatientDietRequirement(**requirement.dict())
    db.add(db_requirement)
    db.commit()
    db.refresh(db_requirement)
    return db_requirement
def update_patient_diet_requirement(db: Session, patient_id: str, requirement: schemas.PatientDietRequirementCreate):
    db_requirement = db.query(models.PatientDietRequirement).filter(models.PatientDietRequirement.patient_id == patient_id).first()
    if db_requirement:
        for key, value in requirement.dict().items():
            setattr(db_requirement, key, value)
        db.commit()
        db.refresh(db_requirement)
    return db_requirement
def get_food_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.FoodItem).offset(skip).limit(limit).all()
def get_food_item(db: Session, food_id: str):
    return db.query(models.FoodItem).filter(models.FoodItem.food_id == food_id).first()
def create_food_item(db: Session, food_item: schemas.FoodItemCreate):
    db_item = models.FoodItem(**food_item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
def search_food_items(db: Session, query: str):
    return db.query(models.FoodItem).filter(
        or_(
            models.FoodItem.name.ilike(f"%{query}%"),
            models.FoodItem.category.ilike(f"%{query}%")
        )
    ).all()
def get_meal_plans(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.MealPlan).offset(skip).limit(limit).all()
def get_meal_plan(db: Session, plan_id: str):
    return db.query(models.MealPlan).filter(models.MealPlan.plan_id == plan_id).first()
def get_patient_meal_plans(db: Session, patient_id: str):
    return db.query(models.MealPlan).filter(models.MealPlan.patient_id == patient_id).all()
def create_meal_plan(db: Session, meal_plan: schemas.MealPlanCreate):
    db_plan = models.MealPlan(**meal_plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan
def get_meals(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Meal).offset(skip).limit(limit).all()
def get_meal(db: Session, meal_id: str):
    return db.query(models.Meal).filter(models.Meal.meal_id == meal_id).first()
def get_meals_by_date(db: Session, date: datetime.date):
    return db.query(models.Meal).filter(models.Meal.meal_date == date).all()
def create_meal(db: Session, meal: schemas.MealCreate):
    db_meal = models.Meal(**meal.dict())
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return db_meal
def update_meal_status(db: Session, meal_id: str, served: bool):
    db_meal = db.query(models.Meal).filter(models.Meal.meal_id == meal_id).first()
    if db_meal:
        db_meal.is_served = served
        if served:
            db_meal.served_at = datetime.utcnow()
        db.commit()
        db.refresh(db_meal)
    return db_meal
def create_meal_item(db: Session, meal_item: schemas.MealItemCreate):
    db_item = models.MealItem(**meal_item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
def get_meal_items(db: Session, meal_id: int):
    return db.query(models.MealItem).filter(models.MealItem.meal_id == meal_id).all()
def get_menus(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Menu).offset(skip).limit(limit).all()
def get_menu(db: Session, menu_id: str):
    return db.query(models.Menu).filter(models.Menu.menu_id == menu_id).first()
def create_menu(db: Session, menu: schemas.MenuCreate):
    db_menu = models.Menu(**menu.dict())
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    return db_menu
def get_menus_by_diet_type(db: Session, diet_type: schemas.DietType):
    return db.query(models.Menu).filter(models.Menu.diet_type == diet_type).all()
def create_menu_item(db: Session, menu_item: schemas.MenuItemCreate):
    db_item = models.MenuItem(**menu_item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
def get_menu_items(db: Session, menu_id: int):
    return db.query(models.MenuItem).filter(models.MenuItem.menu_id == menu_id).all()
def get_nutrition_calculation(db: Session, patient_id: str):
    return db.query(models.NutritionCalculation).filter(models.NutritionCalculation.patient_id == patient_id).first()
def create_nutrition_calculation(db: Session, calculation: schemas.NutritionCalculationCreate):
    db_calc = models.NutritionCalculation(**calculation.dict())
    db.add(db_calc)
    db.commit()
    db.refresh(db_calc)
    return db_calc
def update_nutrition_calculation(db: Session, patient_id: str, calculation: schemas.NutritionCalculationCreate):
    db_calc = db.query(models.NutritionCalculation).filter(models.NutritionCalculation.patient_id == patient_id).first()
    if db_calc:
        for key, value in calculation.dict().items():
            setattr(db_calc, key, value)
        db.commit()
        db.refresh(db_calc)
    return db_calc
def get_dietary_statistics(db: Session):
    total_patients = db.query(models.PatientDietRequirement).count()
    active_meal_plans = db.query(models.MealPlan).filter(models.MealPlan.is_active == True).count()
    meals_served_today = db.query(models.Meal).filter(
        and_(
            models.Meal.meal_date == datetime.utcnow().date(),
            models.Meal.is_served == True
        )
    ).count()
    total_food_items = db.query(models.FoodItem).count()
    return schemas.DietaryStatistics(
        total_patients=total_patients,
        active_meal_plans=active_meal_plans,
        meals_served_today=meals_served_today,
        total_food_items=total_food_items,
        low_stock_items=0  
    )
def get_dietary_dashboard(db: Session):
    todays_meals = db.query(models.Meal).filter(models.Meal.meal_date == datetime.utcnow().date()).count()
    pending_meals = db.query(models.Meal).filter(
        and_(
            models.Meal.meal_date == datetime.utcnow().date(),
            models.Meal.is_served == False
        )
    ).count()
    special_diets = db.query(models.PatientDietRequirement).filter(
        models.PatientDietRequirement.diet_type != schemas.DietType.REGULAR
    ).count()
    nutrition_calculations_today = db.query(models.NutritionCalculation).filter(
        models.NutritionCalculation.calculation_date == datetime.utcnow().date()
    ).count()
    return schemas.DietaryDashboard(
        todays_meals=todays_meals,
        pending_meals=pending_meals,
        special_diets=special_diets,
        nutrition_calculations_today=nutrition_calculations_today
    )