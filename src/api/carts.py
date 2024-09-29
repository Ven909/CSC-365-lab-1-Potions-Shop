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
cart_id = 0
cart_table = {} 

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

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    global cart_id 
    global cart_table

    cart_id += 1
    cart_table[cart_id] = {}

    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    
    if (cart_id not in cart_table):
        cart_table[cart_id] = {}
    using_cart = cart_table[cart_id]
    using_cart[item_sku] = cart_item.quantity
    
    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    # green potion cart checkout
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
            print("Out of potions! Come back later.")
            return "Out of potions! Come back later."
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

    return {"total_potions_bought": 1, "total_gold_paid": 50}
    