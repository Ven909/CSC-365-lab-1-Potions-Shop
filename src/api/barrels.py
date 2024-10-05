from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db



router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
       result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
       
    row = result.fetchone()
    current_gold = row.gold
    green_amt = row.num_green_ml
    red_amt = row.num_red_ml
    blue_amt = row.num_blue_ml

    print(f"Existing Inventory: (green: {green_amt}ml) (red: {red_amt}ml) (blue: {blue_amt} ml) (gold: {current_gold}coins)")

    barrel_cost = 0
    added_green = 0
    added_red = 0
    added_blue = 0

    for barrel in barrels_delivered:
        if current_gold >= barrel.price:
            if barrel.potion_type == [0, 1, 0, 0]:
                added_green += (barrel.ml_per_barrel * barrel.quantity)
            elif barrel.potion_type == [1, 0, 0, 0]:
                added_red += (barrel.ml_per_barrel * barrel.quantity)
            elif barrel.potion_type == [0, 0, 1, 0]:
                added_blue += (barrel.ml_per_barrel * barrel.quantity)
            barrel_cost += (barrel.price * barrel.quantity)
        else:
            return "not enough gold"

    # deduct gold
    updated_gold = current_gold - barrel_cost
    updated_num_green_ml = green_amt + added_green
    updated_num_red_ml = red_amt + added_red
    updated_num_blue_ml = blue_amt + added_blue

    # update table
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {updated_num_green_ml}, num_red_ml = {updated_num_red_ml}, num_blue_ml = {updated_num_blue_ml}, gold = {updated_gold}"))

    print(f"Updated Inventory: (green: {updated_num_green_ml}ml) (red: {updated_num_red_ml}ml) (blue: {updated_num_blue_ml} ml) (gold: {updated_gold}coins)")    
        
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    barrel_plan = []

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).first()

        green_potions = result.num_green_potions
        red_potions = result.num_red_potions
        blue_potions = result.num_blue_potions
        
        gold = result.gold

    # extend the "Buy if less than 10 potions" plan to Red, Green & Blue
    if (green_potions < 10):
        for barrel in wholesale_catalog:
            if "green" in barrel.sku.lower():
                if gold >= barrel.price:
                    barrel_plan.append({"sku": barrel.sku, "quantity": 1,})
                    gold -= barrel.price
    if (red_potions < 10):
        for barrel in wholesale_catalog:
            if "red" in barrel.sku.lower():
                if gold >= barrel.price:
                    barrel_plan.append({"sku": barrel.sku, "quantity": 1,})
                    gold -= barrel.price                
    if (blue_potions < 10):
        for barrel in wholesale_catalog:
            if "blue" in barrel.sku.lower():
                if gold >= barrel.price:
                    barrel_plan.append({"sku": barrel.sku, "quantity": 1,})
                    gold -= barrel.price

    return barrel_plan
    '''
    # V1 green potion code 
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions, gold FROM global_inventory")).first()
        green_potions = result.num_green_potions
        gold = result.gold
    
    # version 1: working for insufficent gold less than 10 potions
    if (green_potions < 10):
        for barrel in wholesale_catalog:
            if barrel.sku == "SMALL_GREEN_BARREL":  # maybe this will fix PDT - PURCHASE_BARRELS
                if gold >= barrel.price:
                    return [
                        {
                            "sku": "SMALL_GREEN_BARREL",
                            "quantity": 1,
                        }
                    ]
                else:
                    print("Insufficient GOLD!")

    return [] 
    '''
    '''
    with db.engine.begin() as connection:
        green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).first()[0]
    
    if (green_potions < 10):
        return [
            {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
            }
        ]
    else:
        return -1 
    '''