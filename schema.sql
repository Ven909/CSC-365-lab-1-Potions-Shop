create table
  public.global_inventory (
    id bigint generated by default as identity,
    num_red_ml integer null default 0,
    gold integer null default 100,
    num_green_ml integer null default 0,
    num_blue_ml integer null default 0,
    num_dark_ml bigint null default '0'::bigint,
    constraint global_inventory_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.potion_catalog (
    id bigint generated by default as identity not null,
    sku text null default ''::text,
    red bigint null,
    green bigint null default '0'::bigint,
    blue bigint null,
    dark bigint null,
    quantity bigint null,
    price bigint null,
    name text null,
    constraint catalog_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.cart_items (
    id bigint generated by default as identity,
    created_at timestamp with time zone not null default now(),
    cart_id bigint null,
    potion_id bigint null,
    quantity bigint null default '0'::bigint,
    sku text null,
    checkout_completed boolean null default false,
    constraint cart_items_pkey primary key (id),
    constraint cart_items_cart_id_fkey foreign key (cart_id) references carts (cart_id),
    constraint cart_items_potion_id_fkey foreign key (potion_id) references potion_catalog (id)
  ) tablespace pg_default;

create table
  public.carts (
    cart_id bigint generated by default as identity,
    customer_name text null,
    constraint carts_pkey primary key (cart_id)
  ) tablespace pg_default;