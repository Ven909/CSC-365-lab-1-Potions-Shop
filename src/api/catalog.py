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

    with db.engine.begin() as connection:
        results = connection.execute(sqlalchemy.text("SELECT potion_id, SUM(inventory_change) AS inventory FROM potion_ledger GROUP BY potion_id"))
        
        for potion in results:
            potion_sql = connection.execute(sqlalchemy.text("SELECT * from potions WHERE potion_id = :potion_id"),
                                            [{"potion_id": potion.potion_id}]).first()
            if potion.inventory > 0:
                catalog.append({
                    "sku": potion_sql.item_sku,
                    "name": potion_sql.name,
                    "quantity": potion.inventory,
                    "price": potion_sql.price,
                    "potion_type": [potion_sql.red_ml, potion_sql.green_ml, potion_sql.blue_ml, potion_sql.dark_ml],
                })

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