CREATE TABLE stg_transactions (
    order_index TEXT,
    order_code TEXT,
    provider_code TEXT,
    location_code TEXT,
    location_name TEXT,
    location_address TEXT,
    buyer TEXT,
    product_order TEXT,
    barcode TEXT,
    product_name TEXT,
    winmart_price NUMERIC,
    product_quantity NUMERIC,
    order_date DATE,
    demand_date DATE
);

-- Bảng này chứa toàn bộ thông tin của sheet sản phẩm
CREATE TABLE stg_product (
    product_code TEXT,
    product_name TEXT,
    product_category_name TEXT,
    product_brand_name TEXT
);

CREATE TABLE stg_base_price (
    barcode TEXT,
    product_code TEXT,
    base_price DECIMAL,
    system_name TEXT
);

CREATE TABLE stg_promotion_detail (
    post_name TEXT,
    system_name TEXT,
    promo_scope TEXT,
    start_date DATE,
    end_date DATE,
    barcode TEXT,
    discount_percentage DECIMAL,
    promo_type_name TEXT,
    promo_product_code TEXT
);

CREATE TABLE stg_delivery_location (
    location_code TEXT,
    system_name TEXT,
    location_name TEXT,
    location_address TEXT,
    customer_code TEXT
);

CREATE TABLE stg_customer (
    customer_code TEXT,
    customer_name TEXT,
    branch_name TEXT,
    product_brand_name TEXT,
    warehouse_code TEXT
);

CREATE TABLE stg_cost_center (
    product_category_name TEXT,
    branch_name TEXT,
    cost_center_code TEXT,
    cost_center_name TEXT
)