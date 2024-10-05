from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).first()

        green_amt = result.num_green_ml
        green_potions = result.num_green_potions
        
        red_amt = result.num_red_ml
        red_potions = result.num_red_potions
        
        blue_amt = result.num_blue_ml
        blue_potions = result.num_blue_potions

    print(f"Existing Inventory: (green: {green_amt}ml) (red: {red_amt}ml) (blue: {blue_amt} ml)")
    print(f"Existing Inventory: (green: {green_potions} potions) (red: {red_potions} potions) (blue: {blue_potions} potions)")

    for potion in potions_delivered:
        #if potion.potion_type[0] != 0:
        if red_amt >= 100 and potion.potion_type == [100,0,0,0]:
            red_amt -= 100 * potion.quantity 
            red_potions += potion.quantity
        #if potion.potion_type[1] != 0:
        elif green_amt >= 100 and potion.potion_type == [0,100,0,0]:
            green_amt -= 100 * potion.quantity 
            green_potions += potion.quantity
        #if potion.potion_type[2] != 0:
        elif blue_amt >= 100 and potion.potion_type == [0,0,100,0]:
            blue_amt -= 100 * potion.quantity 
            blue_potions += potion.quantity

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :green_ml, num_green_potions = :green_potions, num_red_ml =  :red_ml, num_red_potions = :red_potions, num_blue_ml = :blue_ml, num_blue_potions = :blue_potions"), 
                           { "green_ml" : green_amt, "green_potions": green_potions, "red_ml" : red_amt, "red_potions": red_potions, "blue_ml" : blue_amt, "blue_potions": blue_potions,})
    
    print(f"Updated Inventory: (green: {green_amt}ml) (red: {red_amt}ml) (blue: {blue_amt} ml)")
    print(f"Updated Inventory: (green: {green_potions} potions) (red: {red_potions} potions) (blue: {blue_potions} potions)")

    '''
    # V1 green potion code 
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_green_potions FROM global_inventory "))
                                                    
    row = result.fetchone()
    num_green_ml = row.num_green_ml
    num_green_potions = row.num_green_potions

    for potion in potions_delivered:
        num_green_potions += potion.quantity
        if num_green_ml >= 100:
            num_green_ml -= (100 * potion.quantity )
        else:
            return "not enough ml to make potion"
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {num_green_potions}, num_green_ml = {num_green_ml}"))
    '''
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into green potions.

    bottle_plan = []

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).first()
        
        green_amt = result.num_green_ml // 100
        red_amt = result.num_red_ml // 100
        blue_amt = result.num_blue_ml // 100

        if green_amt > 0:
            bottle_plan.append(
            {
                "potion_type": [0, 100, 0, 0], 
                "quantity": green_amt, 
            })
        if red_amt > 0:
            bottle_plan.append(
            {
                "potion_type": [100, 0, 0, 0], 
                "quantity": red_amt, 
            })
        if blue_amt > 0:
            bottle_plan.append(
            {
                "potion_type": [0, 0, 100, 0], 
                "quantity": blue_amt, 
            })
    return bottle_plan

    '''
    # V1 green potion code 
    with db.engine.begin() as connection:
         curr_green = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).first()[0]

    Green_amount = curr_green // 100
    
    # maybe to fix PDT - MIX_POTIONS error?? or APIspec may want an integer?
    if Green_amount > 0:
        return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": Green_amount,
            }
        ]
    
    return []
    '''
    '''
    if Green_amount == 0:
        return []

    return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": Green_amount,
            }
        ]
    '''
if __name__ == "__main__":
    print(get_bottle_plan())
