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
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_green_potions FROM global_inventory "))
                                                    
    row = result.fetchone()
    num_green_ml = row.num_green_ml
    num_green_potions = row.num_green_potions

    for potion in potions_delivered:
        num_green_potions += potion.quantity
        num_green_ml -= (100 * potion.quantity )
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {num_green_potions}, num_green_ml = {num_green_ml}"))

    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

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
    with db.engine.begin() as connection:
         curr_green = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).first()[0]

    Green_amount = curr_green // 100

    # maybe to fix PDT - MIX_POTIONS error?? or APIspec may want an integer?
    if Green_amount == 0:
        return []

    return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": Green_amount,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())
