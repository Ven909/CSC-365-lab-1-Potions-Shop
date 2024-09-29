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
        for barrel in barrels_delivered:
            barrelsUpdated = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml + ({barrels_delivered[0].ml_per_barrel} * {barrels_delivered[0].quantity})")),
            goldUpdated = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - ({barrels_delivered[0].price} * {barrels_delivered[0].quantity})"))
    
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions, gold FROM global_inventory")).first()
        green_potions = result.num_green_potions
        gold = result.gold
    
    # version 1: working for insufficent gold less than 10 potions
    if (green_potions < 10):
        for barrel in wholesale_catalog:
            if gold >= barrel.price:
                return [
                    {
                        "sku": "SMALL_GREEN_BARREL",
                        "quantity": 1,
                    }
                ]
            else:
                print("Insufficient GOLD!")
    else:
        return -1 
    
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