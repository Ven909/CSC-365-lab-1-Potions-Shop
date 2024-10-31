from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    print(f"Before = Total Potions: {total_potions} Total ML: {total_ml} Total Gold: {curr_gold}")

    total_potions = 0

    with db.engine.begin() as connection:
        potion_sql = connection.execute(sqlalchemy.text("SELECT potion_id, SUM(inventory_change) AS inventory FROM potion_ledger GROUP BY potion_id"))
        
        for potion in potion_sql:
            total_potions += potion.inventory
        
        curr_gold = connection.execute(sqlalchemy.text("SELECT SUM(gold_difference) FROM global_ledger")).first()[0]
        curr_ml = connection.execute(sqlalchemy.text(
            """
            SELECT 
            SUM(red_difference) as red_ml, 
            SUM(green_difference) as green_ml,
            SUM(blue_difference) as blue_ml,
            SUM(dark_difference) as dark_ml 
            FROM global_ledger
            """)).first()
        
        total_ml = curr_ml.red_ml + curr_ml.green_ml + curr_ml.blue_ml + curr_ml.dark_ml
    
    print(f"After = Total Potions: {total_potions} Total ML: {total_ml} Total Gold: {curr_gold}")

    return {"number_of_potions": total_potions, "ml_in_barrels": total_ml, "gold": curr_gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        curr_ml = connection.execute(sqlalchemy.text(
            """
            SELECT 
            SUM(red_difference) as red_ml, 
            SUM(green_difference) as green_ml,
            SUM(blue_difference) as blue_ml,
            SUM(dark_difference) as dark_ml 
            FROM global_ledger
            """)).first()

        curr_gold = connection.execute(sqlalchemy.text("SELECT SUM(gold_difference) FROM global_ledger")).first()[0]
        
        total_ml = curr_ml.red_ml + curr_ml.green_ml + curr_ml.blue_ml + curr_ml.dark_ml
        
        total_potions = 0
        potion_sql = connection.execute(sqlalchemy.text("SELECT potion_id, SUM(inventory_change) AS inventory FROM potion_ledger GROUP BY potion_id"))
        
        for potion in potion_sql:
            total_potions += potion.inventory

        needed_gold = max(curr_gold - 3800, 0)
        
        potion_capacity = 0
        ml_capacity = 0
        run_or_not = True
        
        if curr_gold >= 4000:
            potion_capacity = 1
            ml_capacity = 1
            run_or_not = False

        while needed_gold >= 1000 and run_or_not:
            run_or_not = False
            if total_potions >= 40:
                potion_capacity += 1
                needed_gold -= 1000
                run_or_not = True
            
            if needed_gold < 1000:
                break

            if total_ml >= 9000:
                ml_capacity += 1
                needed_gold -= 1000
                run_or_not = True

    return {
        "potion_capacity": potion_capacity,
        "ml_capacity": ml_capacity
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        used_gold = (capacity_purchase.ml_capacity + capacity_purchase.potion_capacity) * 1000
        
        connection.execute(sqlalchemy.text("""INSERT INTO global_ledger (gold_difference, potion_capacity, ml_capacity, order_id, order_type) 
            VALUES (:gold_difference, :potion_capacity, :ml_capacity, :order_id, :order_type) """),
            [{"gold_difference": -used_gold,
              "potion_capacity": capacity_purchase.potion_capacity * 50,
              "ml_capacity": capacity_purchase.ml_capacity * 10000,
              "order_id": order_id,
              "order_type": "Capacity Delivery"}])

    return "OK"
