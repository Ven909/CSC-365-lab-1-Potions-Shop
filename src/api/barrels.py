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

    #with db.engine.begin() as connection:
        
    red_ml = 0
    green_ml = 0
    blue_ml = 0
    dark_ml = 0
    gold = 0

    for barrel_delivered in barrels_delivered:
        print(f'Purchased {barrel_delivered.quantity} of {barrel_delivered.sku}({barrel_delivered.ml_per_barrel}ml)')

        gold -= barrel_delivered.price * barrel_delivered.quantity

        if barrel_delivered.potion_type == [100,0,0,0]:
            red_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
            print(f'Adding {red_ml}ml of red')
        elif barrel_delivered.potion_type == [0,100,0,0]:
            green_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
            print(f'Adding {green_ml}ml of green')
        elif barrel_delivered.potion_type == [0,0,100,0]:
            blue_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
            print(f'Adding {blue_ml}ml of blue')
        elif barrel_delivered.potion_type == [0,0,0,100]:
            dark_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
            print(f'Adding {dark_ml}ml of dark')
        else:
            raise Exception("Invalid potion type")
    
    with db.engine.begin() as connection:        
        connection.execute(sqlalchemy.text(
                """
                INSERT INTO global_ledger
                (gold_difference, red_difference, green_difference, blue_difference, dark_difference, order_id, order_type)
                VALUES (:gold, :red_ml, :green_ml, :blue_ml, :dark_ml, :order_id, :order_type)
                """), 
            {  
                "gold": gold,
                "red_ml": red_ml, 
                "green_ml": green_ml, 
                "blue_ml": blue_ml, 
                "dark_ml": dark_ml,
                "order_id": order_id,
                "order_type": "Barrels"
            })    
    
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    
    barrel_plan = []

    barrel_temp = {
        'red' : None,
        'green' : None,
        'blue' : None,
        'dark' : None}
    
    barrel_split = {
        'large' : barrel_temp.copy(),
        'medium' : barrel_temp.copy(),
        'small' : barrel_temp.copy(),
        'mini' : barrel_temp.copy()}
    
    ml_request = {
        'red' : 0,
        'green' : 0,
        'blue' : 0,
        'dark' : 0}
    
    type = list(ml_request.keys())

    # figure out what barrels to buy
    for barrel in wholesale_catalog:
        
        print(barrel, flush=True)
        
        if barrel.ml_per_barrel == 10000:
            barrel_split['large'][type[barrel.potion_type.index(max(barrel.potion_type))]] = barrel
        elif barrel.ml_per_barrel == 2500:
            barrel_split['medium'][type[barrel.potion_type.index(max(barrel.potion_type))]] = barrel
        elif barrel.ml_per_barrel == 500:
            barrel_split['small'][type[barrel.potion_type.index(max(barrel.potion_type))]] = barrel
        else:
            barrel_split['mini'][type[barrel.potion_type.index(max(barrel.potion_type))]] = barrel
    
    curr_gold = 0
    with db.engine.begin() as connection:
        curr_gold = connection.execute(sqlalchemy.text("SELECT SUM(gold_difference) FROM global_ledger")).first()[0]
        potion_type = connection.execute(sqlalchemy.text("SELECT potion_id, SUM(inventory_change) AS inventory FROM potion_ledger GROUP BY potion_id"))

        for potion in potion_type:
            if potion.inventory <= 1:
                potion_sql = connection.execute(sqlalchemy.text("SELECT * from potions WHERE potion_id = :potion_id"),
                                            [{"potion_id": potion.potion_id}]).first()
                ml_request['red'] += potion_sql.red_ml
                ml_request['green'] += potion_sql.green_ml
                ml_request['blue'] += potion_sql.blue_ml
                ml_request['dark'] += potion_sql.dark_ml

        ml_request = dict(sorted(ml_request.items(), key=lambda item: item[1]))

    for barrel_type in ml_request.keys():
        for barrel_size in barrel_split.values():
          
            if barrel_size[barrel_type] is not None and (int(curr_gold / barrel_size[barrel_type].price) > 0):
                barrel_plan.append(
                    {
                        "sku": barrel_size[barrel_type].sku,
                        "quantity": 1,
                    }
                )
                curr_gold -= barrel_size[barrel_type].price
                break
    
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