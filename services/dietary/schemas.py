from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
class DietType(str, Enum):
    REGULAR = "regular"
    LOW_SODIUM = "low_sodium"
    DIABETIC = "diabetic"
    LOW_FAT = "low_fat"
    HIGH_PROTEIN = "high_protein"
    LIQUID = "liquid"
    SOFT = "soft"
    PUREED = "pureed"
    RENAL = "renal"
    CARDIAC = "cardiac"
class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
class Allergen(str, Enum):
    NUTS = "nuts"
    DAIRY = "dairy"
    EGGS = "eggs"
    SOY = "soy"
    WHEAT = "wheat"
    FISH = "fish"
    SHELLFISH = "shellfish"
class PatientDietRequirementBase(BaseModel):
    patient_id: str
    diet_type: DietType
    allergens: Optional[List[str]] = None
    restrictions: Optional[str] = None
    preferences: Optional[str] = None
    caloric_requirement: Optional[float] = None
    protein_requirement: Optional[float] = None
    carbohydrate_requirement: Optional[float] = None
    fat_requirement: Optional[float] = None
    fluid_restriction: Optional[float] = None
class PatientDietRequirementCreate(PatientDietRequirementBase):
    pass
class PatientDietRequirement(PatientDietRequirementBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class FoodItemBase(BaseModel):
    food_id: str
    name: str
    category: str
    calories_per_100g: float
    protein_per_100g: float
    carbs_per_100g: float
    fat_per_100g: float
    fiber_per_100g: float
    sodium_per_100g: float
    allergens: Optional[List[str]] = None
    is_vegetarian: bool = False
    is_vegan: bool = False
    is_halal: bool = False
    is_kosher: bool = False
class FoodItemCreate(FoodItemBase):
    pass
class FoodItem(FoodItemBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class MealPlanBase(BaseModel):
    plan_id: str
    patient_id: str
    diet_type: DietType
    start_date: datetime
    end_date: datetime
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
class MealPlanCreate(MealPlanBase):
    pass
class MealPlan(MealPlanBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class MealBase(BaseModel):
    meal_id: str
    plan_id: int
    meal_type: MealType
    meal_date: datetime
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
class MealCreate(MealBase):
    pass
class Meal(MealBase):
    id: int
    is_served: bool
    served_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class MealItemBase(BaseModel):
    meal_id: int
    food_item_id: int
    quantity_grams: float
    calories: float
    protein: float
    carbs: float
    fat: float
class MealItemCreate(MealItemBase):
    pass
class MealItem(MealItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class MenuBase(BaseModel):
    menu_id: str
    name: str
    description: Optional[str] = None
    diet_type: DietType
    meal_type: MealType
    is_template: bool = False
class MenuCreate(MenuBase):
    pass
class Menu(MenuBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class MenuItemBase(BaseModel):
    menu_id: int
    food_item_id: int
    quantity_grams: float
    is_optional: bool = False
class MenuItemCreate(MenuItemBase):
    pass
class MenuItem(MenuItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class NutritionCalculationBase(BaseModel):
    calculation_id: str
    patient_id: str
    calculation_date: datetime
    weight_kg: float
    height_cm: float
    age_years: int
    gender: str
    activity_level: str
    bmr: float
    tdee: float
    caloric_requirement: float
    protein_requirement: float
    carb_requirement: float
    fat_requirement: float
class NutritionCalculationCreate(NutritionCalculationBase):
    pass
class NutritionCalculation(NutritionCalculationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
class DietaryStatistics(BaseModel):
    total_patients: int
    active_meal_plans: int
    meals_served_today: int
    total_food_items: int
    low_stock_items: int
class DietaryDashboard(BaseModel):
    todays_meals: int
    pending_meals: int
    special_diets: int
    nutrition_calculations_today: int