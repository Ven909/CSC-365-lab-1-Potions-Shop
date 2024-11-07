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
    with db.engine.begin() as connection:        
        metadata_obj = sqlalchemy.MetaData()
        carts = sqlalchemy.Table('carts', metadata_obj, autoload_with= db.engine)
        cart_items = sqlalchemy.Table('cart_items', metadata_obj, autoload_with= db.engine)
        potions = sqlalchemy.Table('potions', metadata_obj, autoload_with= db.engine)

        search_result = sqlalchemy.select(
            carts.c.cart_id,
            carts.c.customer_name,
            potions.c.item_sku,
            cart_items.c.quantity,
            carts.c.timestamp,
            (cart_items.c.quantity * potions.c.price).label('line_total')
        ).select_from(
            carts.join(cart_items, carts.c.cart_id == cart_items.c.cart_id)
                 .join(potions, cart_items.c.potion_id == potions.c.potion_id)
        )

        if sort_col is search_sort_options.customer_name:
            sort_parameter = search_result.c.customer_name
        elif sort_col is search_sort_options.item_sku:
            sort_parameter = search_result.c.item_sku
        elif sort_col is search_sort_options.line_item_total:
            sort_parameter = search_result.c.line_total
        elif sort_col is search_sort_options.timestamp:
            sort_parameter = search_result.c.timestamp
        else:
            raise RuntimeError("No Sort Parameter Passed")
        
        search_values = (
            sqlalchemy.select(
                search_result.c.cart_id,
                search_result.c.quantity,
                search_result.c.item_sku,
                search_result.c.line_total,
                search_result.c.timestamp,
                search_result.c.customer_name
            ).select_from(search_result)
        )

        sorted_values = search_values
        if customer_name != "":
            sorted_values = sorted_values.where(
                (search_result.c.customer_name.ilike(f"%{customer_name}%")))
        if potion_sku != "":
            sorted_values = sorted_values.where(
                (search_result.c.item_sku.ilike(f"%{potion_sku}%")))
        if sort_order == search_sort_order.desc: 
            sorted_values = sorted_values.order_by(
                sqlalchemy.desc(sort_parameter) if sort_order == search_sort_order.desc else sqlalchemy.desc(sort_parameter))

        page = 0 if search_page == "" else int(search_page) * 5
        result = connection.execute(search_values.limit(5).offset(page))
        search_return = []
        for row in result:
            search_return.append(
                    {
                        "line_item_id": row.cart_id,
                        "item_sku": f"{row.quantity} {row.item_sku}",
                        "customer_name": row.customer_name,
                        "line_item_total": row.line_total,
                        "timestamp": row.timestamp,
                    })
        
        prev_page = f"{(page//5) - 1}" if (page//5) >= 1 else ""
        next_page = f"{(page//5) + 1}" if (connection.execute(search_values).rowcount - (page)) > 0 else ""
    
    return ({
            "previous": prev_page,
            "next": next_page,
            "results": search_return
        })


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
def create_cart(new_cart: Customer):
    """ """
    '''
    Error creating new cart with code: Returned HTTP Code 422 
    {"message":["['body', 'customer']: field required
    '''
    with db.engine.begin() as connection:
        cart_id = connection.execute(sqlalchemy.text("INSERT INTO carts (customer_name) VALUES (:customer_name) RETURNING cart_id"),
            [{"customer_name": new_cart.customer_name}]).first()[0]

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
        potion_id = connection.execute(sqlalchemy.text("SELECT potion_id FROM potions WHERE item_sku = :item_sku"),
            [{"item_sku": item_sku}]).first()[0]
        
        connection.execute(sqlalchemy.text("INSERT INTO cart_items (cart_id, potion_id, quantity) VALUES (:cart_id, :potion_id, :quantity)"),
            [{"cart_id": cart_id,
              "potion_id": potion_id,
              "quantity": cart_item.quantity}])

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
    print(f"Starting Checkout for Cart {cart_id}:")

    gold_paid = 0
    potions_bought = 0

    with db.engine.begin() as connection:
        cart_sql = connection.execute(sqlalchemy.text("SELECT * FROM cart_items WHERE cart_id = :cart_id"), [{"cart_id": cart_id}])
        
        for item in cart_sql:
            connection.execute(sqlalchemy.text(
                """
                INSERT INTO potion_ledger (potion_id, inventory_change, order_id, order_type) 
                VALUES (:potion_id, :inventory_change, :order_id, :order_type)
                """),
                [{"potion_id": item.potion_id,
                  "inventory_change": -item.quantity,
                  "order_id": cart_id,
                  "order_type": "checkout"}])
            
            potion_cost = connection.execute(sqlalchemy.text("SELECT price FROM potions WHERE potion_id = :potion_id"), 
                                             [{"potion_id": item.potion_id}]).first()[0]
            
            gold_paid += (item.quantity * potion_cost)
            potions_bought += item.quantity
        
        connection.execute(sqlalchemy.text(
            "INSERT INTO global_ledger (gold_difference, order_id, order_type) VALUES (:total_cost, :order_id, :order_type)"), 
            [{"total_cost": gold_paid,
              "order_id": cart_id,
              "order_type": "checkout"}])
    
    print(f"Checkout for Cart {cart_id} is complete.")    
    
    return {"total_potions_bought": potions_bought, "total_gold_paid": gold_paid}  
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

    