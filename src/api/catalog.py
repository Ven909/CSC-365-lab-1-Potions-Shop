from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

# create new tables for red & blue potions

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    # If you have zero potions you should return 
    # an empty array for your catalog (rather than a potion with the quantity as 0)
    catalog = []

    # change num_green_potions to *
    with db.engine.begin() as connection:
        results = connection.execute(sqlalchemy.text("SELECT * FROM potion_catalog")).all()
        
        for potion in results:
            if potion.quantity > 0:
                catalog.append(
                    {
                        "sku": potion.sku,
                        "name": potion.name,
                        "quantity": potion.quantity,
                        "price": potion.price,
                        "potion_type": [potion.red, potion.green, potion.blue, potion.dark]
                    }
                )
    return catalog

    '''
    V2 code
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).first()
    
        green_potions = result.num_green_potions
        red_potions = result.num_red_potions
        blue_potions = result.num_blue_potions
    
    if green_potions != 0:
        catalog.append({
            "sku": "GREEN_POTION",
            "name": "green potion",
            "quantity": green_potions,
            "price": 50,
            "potion_type": [0, 100, 0, 0],
        })
    if red_potions != 0:
        catalog.append({
            "sku": "RED_POTION",
            "name": "red potion",
            "quantity": red_potions,
            "price": 50,
            "potion_type": [100, 0, 0, 0],
        })
    if blue_potions != 0:
        catalog.append({
            "sku": "BLUE_POTION",
            "name": "blue potion",
            "quantity": blue_potions,
            "price": 50,
            "potion_type": [0, 0, 100, 0],
        })
    
    return catalog
    '''
    '''
    # V1 green potion code
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