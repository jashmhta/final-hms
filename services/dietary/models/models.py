import datetime
from sqlalchemy import Column, DateTime, Integer, String, Float, Text, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )


class EncryptedString(String):
    pass


class UserStub(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class DietType(str, enum.Enum):
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


class MealType(str, enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class Allergen(str, enum.Enum):
    NUTS = "nuts"
    DAIRY = "dairy"
    EGGS = "eggs"
    SOY = "soy"
    WHEAT = "wheat"
    FISH = "fish"
    SHELLFISH = "shellfish"


class PatientDietRequirement(Base, TimestampMixin):
    __tablename__ = "patient_diet_requirements"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True)  # Reference to patient in core HMS
    diet_type = Column(Enum(DietType))
    allergens = Column(JSON, nullable=True)  # List of allergens
    restrictions = Column(Text, nullable=True)
    preferences = Column(Text, nullable=True)
    caloric_requirement = Column(Float, nullable=True)
    protein_requirement = Column(Float, nullable=True)
    carbohydrate_requirement = Column(Float, nullable=True)
    fat_requirement = Column(Float, nullable=True)
    fluid_restriction = Column(Float, nullable=True)  # ml per day
    is_active = Column(Boolean, default=True)


class FoodItem(Base, TimestampMixin):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    food_id = Column(String, unique=True)
    name = Column(String)
    category = Column(String)  # protein, carbohydrate, vegetable, etc.
    calories_per_100g = Column(Float)
    protein_per_100g = Column(Float)
    carbs_per_100g = Column(Float)
    fat_per_100g = Column(Float)
    fiber_per_100g = Column(Float)
    sodium_per_100g = Column(Float)
    allergens = Column(JSON, nullable=True)
    is_vegetarian = Column(Boolean, default=False)
    is_vegan = Column(Boolean, default=False)
    is_halal = Column(Boolean, default=False)
    is_kosher = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)


class MealPlan(Base, TimestampMixin):
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(String, unique=True)
    patient_id = Column(String, index=True)
    diet_type = Column(Enum(DietType))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    total_calories = Column(Float)
    total_protein = Column(Float)
    total_carbs = Column(Float)
    total_fat = Column(Float)
    is_active = Column(Boolean, default=True)


class Meal(Base, TimestampMixin):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(String, unique=True)
    plan_id = Column(Integer, ForeignKey("meal_plans.id"))
    meal_type = Column(Enum(MealType))
    meal_date = Column(DateTime)
    total_calories = Column(Float)
    total_protein = Column(Float)
    total_carbs = Column(Float)
    total_fat = Column(Float)
    is_served = Column(Boolean, default=False)
    served_at = Column(DateTime, nullable=True)

    plan = relationship("MealPlan")


class MealItem(Base, TimestampMixin):
    __tablename__ = "meal_items"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id"))
    food_item_id = Column(Integer, ForeignKey("food_items.id"))
    quantity_grams = Column(Float)
    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fat = Column(Float)

    meal = relationship("Meal")
    food_item = relationship("FoodItem")


class Menu(Base, TimestampMixin):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(String, unique=True)
    name = Column(String)
    description = Column(Text, nullable=True)
    diet_type = Column(Enum(DietType))
    meal_type = Column(Enum(MealType))
    is_template = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)


class MenuItem(Base, TimestampMixin):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menus.id"))
    food_item_id = Column(Integer, ForeignKey("food_items.id"))
    quantity_grams = Column(Float)
    is_optional = Column(Boolean, default=False)

    menu = relationship("Menu")
    food_item = relationship("FoodItem")


class NutritionCalculation(Base, TimestampMixin):
    __tablename__ = "nutrition_calculations"

    id = Column(Integer, primary_key=True, index=True)
    calculation_id = Column(String, unique=True)
    patient_id = Column(String)
    calculation_date = Column(DateTime)
    weight_kg = Column(Float)
    height_cm = Column(Float)
    age_years = Column(Integer)
    gender = Column(String)
    activity_level = Column(String)
    bmr = Column(Float)  # Basal Metabolic Rate
    tdee = Column(Float)  # Total Daily Energy Expenditure
    caloric_requirement = Column(Float)
    protein_requirement = Column(Float)
    carb_requirement = Column(Float)
    fat_requirement = Column(Float)
