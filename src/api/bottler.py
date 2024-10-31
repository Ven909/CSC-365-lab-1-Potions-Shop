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

    red_ml = 0
    green_ml = 0
    blue_ml = 0
    dark_ml = 0

    with db.engine.begin() as connection:
        for potion in potions_delivered:
            red_ml -= potion.potion_type[0] * potion.quantity
            green_ml -= potion.potion_type[1] * potion.quantity
            blue_ml -= potion.potion_type[2] * potion.quantity
            dark_ml -= potion.potion_type[3] * potion.quantity
            potion_id = connection.execute(sqlalchemy.text(""" SELECT * FROM potions 
                WHERE red_ml = :red_ml and green_ml = :green_ml and blue_ml = :blue_ml and dark_ml = :dark_ml
                """),
                [{"red_ml": potion.potion_type[0], 
                  "green_ml": potion.potion_type[1],
                  "blue_ml": potion.potion_type[2], 
                  "dark_ml": potion.potion_type[3]}]).first().potion_id
            connection.execute(sqlalchemy.text(
                    """
                    INSERT INTO potion_ledger
                    (potion_id, inventory_change, order_id, order_type)
                    VALUES (:potion_id, :inventory_change, :order_id, :order_type)
                    """), 
                [{  "potion_id": potion_id,
                    "inventory_change": potion.quantity, 
                    "order_id": order_id, 
                    "order_type": "bottling"}])
        
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO global_ledger
                (gold_difference, red_difference, green_difference, blue_difference, dark_difference, order_id, order_type)
                VALUES (:gold, :red_ml, :green_ml, :blue_ml, :dark_ml, :order_id, :order_type)
                """), 
            [{  "gold": 0,
                "red_ml": red_ml, 
                "green_ml": green_ml, 
                "blue_ml": blue_ml, 
                "dark_ml": dark_ml,
                "order_id": order_id,
                "order_type": "Bottling Potions"}])
    '''
    V2 code
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).fetchone()

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
        #while(max_red_potions > potion.quantity and potion.potion_type == [100,0,0,0]): 
        if red_amt >= 100 and potion.potion_type == [100,0,0,0]:
            red_amt -= (100 * potion.quantity) 
            red_potions += potion.quantity
        #if potion.potion_type[1] != 0:
        #elif potion.quantity <= max_green_potions and potion.potion_type == [0,100,0,0]:
        #while(max_green_potions > potion.quantity and potion.potion_type == [100,0,0,0]): 
        elif green_amt >= 100 and potion.potion_type == [0,100,0,0]:
            green_amt -= (100 * potion.quantity) 
            green_potions += potion.quantity
        #if potion.potion_type[2] != 0:
        #elif potion.quantity <= max_blue_potions and potion.potion_type == [0,0,100,0]:
        #while(max_blue_potions > potion.quantity and potion.potion_type == [100,0,0,0]): 
        elif blue_amt >= 100 and potion.potion_type == [0,0,100,0]:
            blue_amt -= (100 * potion.quantity )
            blue_potions += potion.quantity
        else:
            return "not enough ml to make potion"

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {green_amt}, num_green_potions = {green_potions}, num_red_ml = {red_amt}, num_red_potions = {red_potions}, num_blue_ml = {blue_amt}, num_blue_potions = {blue_potions}")) 
                           #,{ "green_ml" : green_amt, "green_potions": green_potions, "red_ml" : red_amt, "red_potions": red_potions, "blue_ml" : blue_amt, "blue_potions": blue_potions,})
    
    print(f"Updated Inventory: (green: {green_amt}ml) (red: {red_amt}ml) (blue: {blue_amt} ml)")
    print(f"Updated Inventory: (green: {green_potions} potions) (red: {red_potions} potions) (blue: {blue_potions} potions)")
    '''
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
    print("Bottle plan: ")

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into green potions.

    bottle_plan = []

    with db.engine.begin() as connection:
        red = connection.execute(sqlalchemy.text("SELECT SUM(red_difference) FROM global_ledger")).first()[0]
        green = connection.execute(sqlalchemy.text("SELECT SUM(green_difference) FROM global_ledger")).first()[0]
        blue = connection.execute(sqlalchemy.text("SELECT SUM(blue_difference) FROM global_ledger")).first()[0]
        dark = connection.execute(sqlalchemy.text("SELECT SUM(dark_difference) FROM global_ledger")).first()[0]
        potion_sql = connection.execute(sqlalchemy.text("SELECT * from potions"))

        available_red = red
        available_green = green
        available_blue = blue
        available_dark = dark

        for potion in potion_sql:
            curr_potions = connection.execute(sqlalchemy.text(
                "SELECT SUM(inventory_change) AS inventory from potion_ledger WHERE potion_id = :potion_id"),
                [{"potion_id": potion.potion_id}]).first()
            
            if curr_potions.inventory is None or curr_potions.inventory <= 1:
                if potion.red_ml <= available_red and potion.green_ml <= available_green \
                and potion.blue_ml <= available_blue and potion.dark_ml <= available_dark:
                    
                    bottle_quantity = how_many_to_bottle(potion, available_red, available_green, available_blue, available_dark)
                    if bottle_quantity > 0:
                        bottle_plan.append({
                            "potion_type": [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml],
                            "quantity": bottle_quantity,
                        })
                        available_red -= potion.red_ml * bottle_quantity
                        available_green -= potion.green_ml * bottle_quantity
                        available_blue -= potion.blue_ml * bottle_quantity
                        available_dark -= potion.dark_ml * bottle_quantity

    return bottle_plan
        
def how_many_to_bottle(potion, available_red, available_green, available_blue, available_dark):    
    half_red = available_red / 2
    half_green = available_green / 2
    half_blue = available_blue / 2
    half_dark = available_dark / 2
    
    # Calculate max bottles for each ingredient, or infinity if ingredient is not needed
    red_made = half_red // potion.red_ml if potion.red_ml > 0 else float('inf')
    green_made = half_green // potion.green_ml if potion.green_ml > 0 else float('inf')
    blue_made = half_blue // potion.blue_ml if potion.blue_ml > 0 else float('inf')
    dark_made = half_dark // potion.dark_ml if potion.dark_ml > 0 else float('inf')
    
    # Return the minimum number of bottles possible based on limiting ingredient
    return int(min(red_made, green_made, blue_made, dark_made))

    '''
    V2 code
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
