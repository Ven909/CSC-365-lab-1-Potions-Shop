from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    # If you have zero potions you should return 
    # an empty array for your catalog (rather than a potion with the quantity as 0)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))

    green_potions = result.first().num_green_potions
    
    # if 0 green potions, return []
    if green_potions == 0:
        return []
    
    #otherwise return catalog items
    return [
            {
                "sku": "GREEN_POTION",
                "name": "green potion",
                "quantity": green_potions,
                "price": 100,
                "potion_type": [0, 100, 0, 0],
            }
        ]

    '''
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
    return [
            {
                "sku": "GREEN_POTION",
                "name": "green potion",
                "quantity": result.fetchone().num_green_potions,
                "price": 100,
                "potion_type": [0, 100, 0, 0],
            }
        ]
    '''