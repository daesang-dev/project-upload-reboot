CREATE TABLE product_brand (
    product_brand_key INTEGER PRIMARY KEY,
    product_brand_name TEXT NOT NULL
);

CREATE TABLE product_category (
    product_category_key INTEGER PRIMARY KEY,
    product_category_name TEXT NOT NULL,
    product_brand_key INTEGER REFERENCES product_brand(product_brand_key)
);

CREATE TABLE product (
	product_code TEXT PRIMARY KEY,
	product_name TEXT NOT NULL,
	product_category_key INTEGER REFERENCES product_category(product_category_key)
);

CREATE TABLE customer_system (
	system_key INTEGER PRIMARY KEY,
	system_name TEXT UNIQUE
);

CREATE TABLE warehouse (
	warehouse_key INTEGER PRIMARY KEY AUTOINCREMENT,
	warehouse_code TEXT UNIQUE
);

CREATE TABLE branch(
	branch_key INTEGER PRIMARY KEY AUTOINCREMENT,
	branch_name TEXT NOT NULL
);

CREATE TABLE customer(
	customer_code TEXT PRIMARY KEY,
	customer_name TEXT NOT NULL,
	branch_key INTEGER REFERENCES branch(branch_key),
	warehouse_key INTEGER REFERENCES warehouse(warehouse_key),
    product_brand_key INTEGER REFERENCES product_brand(product_brand_key)
);

CREATE TABLE delivery_location (
    location_code TEXT PRIMARY KEY,
    location_name TEXT,
    location_address TEXT,
    system_key INTEGER REFERENCES customer_system(system_key)
);

-- Do 1 mã điểm giao có thể gồm 2 code khách hàng Daesang - Đức Việt
CREATE TABLE location_customer (
	location_code TEXT REFERENCES delivery_location(location_code),
	customer_code TEXT REFERENCES customer(customer_code),
    UNIQUE (location_code, customer_code)
);

-- Các bảng liên quan tới chương trình khuyến mãi, giá, giảm giá
CREATE TABLE promotion_type (
	promo_type_key INTEGER PRIMARY KEY,
	promo_type_name TEXT UNIQUE
);

CREATE TABLE base_price (
	barcode TEXT PRIMARY KEY,
	product_code TEXT REFERENCES product(product_code),
	base_price NUMERIC NOT NULL
);

CREATE TABLE promotion_detail (
	post_name TEXT NOT NULL,
	start_date DATE NOT NULL,
	end_date DATE NOT NULL,
    discount_percentage NUMERIC,
    system_key INTEGER REFERENCES customer_system(system_key),
	promo_type_key INTEGER REFERENCES promotion_type(promo_type_key),
    promo_product_code TEXT REFERENCES product(product_code),
	barcode TEXT NOT NULL REFERENCES base_price(barcode)
);

CREATE INDEX idx_promo_date ON promotion_detail(start_date, end_date);
CREATE INDEX idx_loc_stg ON stg_transactions(location_code);
CREATE INDEX idx_barcode_stg ON stg_transactions(barcode);
CREATE INDEX idx_date_stg ON stg_transactions(order_date);

CREATE TABLE cost_center (
    cost_center_code TEXT PRIMARY KEY,
    cost_center_name TEXT UNIQUE,
    branch_key INT REFERENCES branch (branch_key),
    product_category_key INT REFERENCES product_category (product_category_key)
);

CREATE TABLE transactions (
    order_index TEXT NOT NULL,
    order_code TEXT NOT NULL,
    provider_code TEXT NOT NULL,
    location_code TEXT REFERENCES delivery_location(location_code),
    location_name TEXT NOT NULL,
    location_address TEXT NOT NULL,
    buyer TEXT,
    product_order TEXT NOT NULL,
    barcode TEXT REFERENCES base_price(barcode) NOT NULL,
    product_name TEXT NOT NULL,
    winmart_price NUMERIC NOT NULL,
    product_quantity NUMERIC NOT NULL,
    order_date DATE NOT NULL NOT NULL,
    demand_date DATE
);