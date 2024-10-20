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
    
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
       result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
       
    row = result.fetchone()
    current_gold = row.gold

    barrel_cost = 0
    added_green = 0
    added_red = 0
    added_blue = 0
    added_dark = 0

    for barrel in barrels_delivered:
        print(f'Puchased {barrel.quantity} of {barrel.sku}({barrel.ml_per_barrel}ml)')

        barrel_cost += barrel.quantity * barrel.price

        # TODO: maybe this part is what's preventing bottler
        if current_gold >= barrel.price:
            if (barrel.potion_type == [1, 0, 0, 0]): # Red
                added_red += barrel.quantity * barrel.ml_per_barrel
                print(f'Adding {added_red}ml of red')
            elif (barrel.potion_type == [0, 1, 0, 0]): # Green
                added_green += barrel.quantity * barrel.ml_per_barrel
                print(f'Adding {added_green}ml of green')
            elif (barrel.potion_type == [0, 0, 1, 0]): # Blue
                added_blue += barrel.quantity * barrel.ml_per_barrel
                print(f'Adding {added_blue}ml of blue')
            elif(barrel.potion_type == [0, 0, 0, 1]): # Dark
                added_dark += barrel.quantity * barrel.ml_per_barrel
                print(f'Adding {added_dark}ml of dark')
            else:
                raise Exception("Invalid Potion Type")
        else:
            return "not enough gold"    

    # Updates
    with db.engine.begin() as connection:
        result = """UPDATE global_inventory
                        SET num_red_ml = num_red_ml + :added_red,
                        num_green_ml = num_green_ml + :added_green,
                        num_blue_ml = num_blue_ml + :added_blue,
                        num_dark_ml = num_dark_ml + :added_dark,
                        gold = gold - :barrel_cost"""
    
        connection.execute(sqlalchemy.text(result), 
            [{"added_red": added_red, "added_green": added_green, "added_blue": added_blue, "added_dark": added_dark, "barrel_cost": barrel_cost}])

    """ 
    V2 code
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
    """    
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    
    barrel_plan = []

    catalog_sorted = barrel_sort(wholesale_catalog)
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""SELECT * FROM global_inventory""")).one()
        
        green_ml = result.num_green_ml
        red_ml = result.num_red_ml
        blue_ml = result.num_blue_ml
        dark_ml = result.num_dark_ml

        curr_gold = result.gold
    
    print(f"Current Gold: {result.gold}")

    curr_red = ("red", [100, 0 , 0, 0], red_ml)
    curr_green = ("green", [0, 100 , 0, 0], green_ml)
    curr_blue = ("blue", [0, 0 , 100, 0], blue_ml)
    curr_dark = ("dark", [0, 0 , 0, 100], dark_ml) 
    
    priority = [curr_red, curr_green, curr_blue, curr_dark]

    priority.sort(key = lambda list: list[2])

    # Buying barrels
    for i in range(len(priority)):
        potion_color = priority[i][0]
        potion_inventory = priority[i][2]
        
        if potion_color not in catalog_sorted:
            print(f"There are no {potion_color} barrels for sale currently")
            
            continue

        catalog_choice = catalog_sorted[potion_color]

        curr_request, curr_gold = balance_plan(priority[i], catalog_choice, curr_gold)
        
        barrel_plan.extend(curr_request)
        
        print(f"Inventory Gold: {curr_gold}")

    print(f'Requesting Barrels: \n{barrel_plan}')
    
    return barrel_plan
    '''
    V2 code
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).first()

        green_potions = result.num_green_potions
        red_potions = result.num_red_potions
        blue_potions = result.num_blue_potions
        
        gold = result.gold
    
    # THIS works with small green barrel but ^^^ trying something new
    # extend the "Buy if less than 10 potions" plan to Red, Green & Blue
    if (green_potions < 10):
        for barrel in wholesale_catalog:
            #if "green" in barrel.sku.lower():
            if barrel.sku == "SMALL_GREEN_BARREL":
                if gold >= barrel.price:
                    barrel_plan.append({"sku": "SMALL_GREEN_BARREL", "quantity": 1,})
                    gold -= barrel.price
    if (red_potions < 10):
        for barrel in wholesale_catalog:
            #if "red" in barrel.sku.lower():
            if barrel.sku == "SMALL_RED_BARREL":
                if gold >= barrel.price:
                    barrel_plan.append({"sku": "SMALL_RED_BARREL", "quantity": 1,})
                    gold -= barrel.price                
    if (blue_potions < 10):
        for barrel in wholesale_catalog:
            #if "blue" in barrel.sku.lower():
            if barrel.sku == "SMALL_BLUE_BARREL":
                if gold >= barrel.price:
                    barrel_plan.append({"sku": "SMALL_BLUE_BARREL", "quantity": 1,})
                    gold -= barrel.price

    return barrel_plan
    '''
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
def balance_plan(curr_priority, catalog_choice, curr_gold):
    requests = []
    quantity = 0

    wanted_ml = 0
    curr_ml = curr_priority[2]
    max_ml = 5000 - curr_ml
    
    for barrel in catalog_choice:
        good_request = []
        good_request.append(barrel.quantity) 
        good_request.append(curr_gold // barrel.price) 
        good_request.append(max_ml // barrel.ml_per_barrel) 
        quantity = min(good_request) 

        if quantity > 0: 
            requests.append(
                {
                    "sku": barrel.sku,
                    "quantity": quantity
                })
            curr_gold -= (quantity * barrel.price)
            wanted_ml += quantity * barrel.ml_per_barrel
            max_ml -= wanted_ml

    return requests, curr_gold
        

def barrel_sort(wholesale_catalog: list[Barrel]):
    catalog_sorted = {}
    
    for barrel in wholesale_catalog:
        if (barrel.potion_type == [1, 0, 0, 0]):
            if ("red" not in catalog_sorted):
                catalog_sorted["red"] = [barrel]
            else:
                catalog_sorted["red"].append(barrel)
        elif (barrel.potion_type == [0, 0, 1, 0]):
            if ("blue" not in catalog_sorted):
                catalog_sorted["blue"] = [barrel]
            else:
                catalog_sorted["blue"].append(barrel)
        elif (barrel.potion_type == [0, 1, 0, 0]):
            if ("green" not in catalog_sorted):
                catalog_sorted["green"] = [barrel]
            else:
                catalog_sorted["green"].append(barrel)
        elif (barrel.potion_type == [0, 0, 0, 1]):
            if ("dark" not in catalog_sorted):
                catalog_sorted["dark"] = [barrel]
            else:
                catalog_sorted["dark"].append(barrel)
        else:
            raise Exception("Invalid Potion Type")
    
    return catalog_sorted