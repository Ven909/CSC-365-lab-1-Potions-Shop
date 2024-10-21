from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

# make a global cart ID variable for ease
'''
V2 code
cart_id = 0
cart_table = {} 
'''

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

class NewCart(BaseModel):
    customer: str

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"



@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    cart_sql = """INSERT INTO carts (customer_name) VALUES (:name) RETURNING cart_id"""
    with db.engine.begin() as connection:
        cart_id = connection.execute(sqlalchemy.text(cart_sql), [{"name": new_cart.customer}]).scalar_one()
    
    print(f"New Cart_ID added: {cart_id}")
    '''
    V2 code
    global cart_id
    cart_id += 1
    cart_table[cart_id] = {}
    '''

    '''
    # V1 green potion code
    global cart_id 
    global cart_table

    cart_id += 1
    cart_table[cart_id] = {}
    '''
    
    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int

@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    return {}

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    print("Setting Item Quantity:")

    with db.engine.begin() as connection:
        result = """INSERT INTO cart_items (cart_id, potion_id, quantity, sku)
                    SELECT :cart_id, potion_catalog.id, :quantity, :item_sku
                    FROM potion_catalog WHERE potion_catalog.sku = :item_sku"""
        
        connection.execute(sqlalchemy.text(result), 
                           [{"cart_id": cart_id, "quantity": cart_item.quantity, "item_sku": item_sku}])

    print(f"Added {cart_item.quantity} {item_sku} in Cart {cart_id}")
    '''
    V2 code
    if cart_id not in cart_table:
        cart_table[cart_id] = {}

    using_cart = cart_table[cart_id]
    using_cart[item_sku] = cart_item.quantity
    '''

    '''
    # V1 green potion code
    if (cart_id not in cart_table):
        cart_table[cart_id] = {}
    using_cart = cart_table[cart_id]
    using_cart[item_sku] = cart_item.quantity
    '''
    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    transaction_gold = 0

    print(f"Starting Checkout for Cart {cart_id}:")

    with db.engine.begin() as connection:
        #go into the cart_items and filter out all the items that are from the current cart
        cart_stuff = connection.execute(sqlalchemy.text("""SELECT * FROM cart_items WHERE cart_id = :cart_id"""), [{"cart_id": cart_id}]).all()

        for item in cart_stuff:
            potion_result = connection.execute(sqlalchemy.text("""SELECT quantity, price FROM potion_catalog WHERE id = :potion_id"""), [{"potion_id": item.potion_id}]).one()

            if item.quantity > potion_result.quantity:
                connection.execute(sqlalchemy.text("""UPDATE cart_items SET quantity = :inventory_quant WHERE cart_id = :cart_id and potion_id = :potion_id"""), 
                                                    [{"cart_id": cart_id, "potion_id": item.potion_id}])
                
            connection.execute(sqlalchemy.text("""UPDATE potion_catalog SET quantity = quantity - :bought_pots WHERE id = :potion_id """), 
                                                    [{"potion_id": item.potion_id, "bought_pots": item.quantity}])

            transaction_gold = potion_result.price * item.quantity
            connection.execute(sqlalchemy.text("""UPDATE global_inventory SET gold = gold + :transaction_gold"""), [{"transaction_gold": transaction_gold}])

            connection.execute(sqlalchemy.text("""UPDATE cart_items SET checkout_completed = true WHERE cart_id = :cart_id and potion_id = :potion_id"""), 
                                                    [{"potion_id": item.potion_id, "cart_id": cart_id}])
            
            print(f"Cart {cart_id} bought {item.quantity} {item.sku} for {transaction_gold}")
    
    print(f"Checkout for Cart {cart_id} is complete.")
    return "OK"
    '''
    V2 code
    if cart_id not in cart_table:
        cart_table[cart_id] = {}

    using_cart = cart_table[cart_id]

    # stats for the specific transaction:
    bought_pots = 0
    transaction_gold = 0

    green_pots = 0
    red_pots = 0
    blue_pots = 0
    gold = 0

    with db.engine.begin() as connection:
        for sku, quantity in using_cart.items():
            result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).first()

            green_pots = result.num_green_potions
            red_pots = result.num_red_potions
            blue_pots = result.num_blue_potions
            gold = result.gold
        
            if "green" in sku.lower():
                print("Customer buys green")
                if green_pots >= quantity:
                    green_pots -= quantity
                    bought_pots += quantity
                    transaction_gold += quantity * 50
                else:
                    bought_pots += green_pots
                    transaction_gold += green_pots * 50
                    green_pots = 0
            
            if "red" in sku.lower():
                print("Customer buys red")
                if red_pots >= quantity:
                    red_pots -= quantity
                    bought_pots += quantity
                    transaction_gold += quantity * 50
                else:
                    bought_pots += red_pots
                    transaction_gold += red_pots * 50
                    red_pots = 0

            if "blue" in sku.lower():
                print("Customer buys blue")
                if blue_pots >= quantity:
                    blue_pots -= quantity
                    bought_pots += quantity
                    transaction_gold += quantity * 50
                else:
                    bought_pots += blue_pots
                    transaction_gold += blue_pots * 50
                    blue_pots = 0
            
            gold += transaction_gold

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = :green_potions, num_red_potions = :red_potions, num_blue_potions = :blue_potions, gold = :gold"), 
                           { "green_potions": green_pots, "red_potions": red_pots, "blue_potions": blue_pots, "gold": gold})
    
    return {"total_potions_bought": bought_pots, "total_gold_paid": transaction_gold}
    '''
    '''
    # V1: green potion cart checkout
    with db.engine.begin() as connection: 
        sql_to_execute = \
            """SELECT * 
            FROM global_inventory;
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))
        data = result.fetchall() 
        num_green_potions = data[0][0]
        gold = data[0][2]
        # if 0 inventory...
        if num_green_potions == 0:
            print("Sorry, we're currently out of potions")
            return "Sorry, we're currently out of potions"
        # otherwise, authorize transaction
        sql_to_execute = \
            f"""UPDATE global_inventory
            SET num_green_potions = {num_green_potions - 1},
            gold = {gold + 50};
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))
        
        # show transaction details 
        sql_to_execute = \
            """SELECT * 
            FROM global_inventory;
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))
        data = result.fetchall() 
        print("Checkout Result: ", data) 
    '''
    '''
    using_cart = cart_table[cart_id]

    with db.engine.begin() as connection:
        for quantity in using_cart.values():
            result = connection.execute(sqlalchemy.text("SELECT num_green_potions, gold FROM global_inventory")).first()
            curr_grn_potions = result.num_green_potions
            curr_gold = result.gold

        # if sufficient inventory of green, authorize payment
        if curr_grn_potions >= quantity:
            curr_grn_potions -= quantity        # adequate green deducted
            curr_gold += quantity * 50         # 50 coins added to inventory 

        # stats for the specific transaction:
        bought_pots = 0
        transaction_gold = 0
        
        bought_pots += quantity
        transaction_gold += quantity * 50

    # update green barrel & gold inventory after the transaction
    connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :curr_gold"), [{"curr_gold": curr_gold }])
    connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = :curr_grn_potions"))
    '''

    