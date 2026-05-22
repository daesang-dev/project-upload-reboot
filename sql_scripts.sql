-- Các bảng có mối quan hệ trực tiếp sản phẩm
CREATE TABLE product_category (
    product_category_key INTEGER PRIMARY KEY,
    ctg_1 TEXT,
    ctg_2 TEXT
);

CREATE TABLE product (
	product_code TEXT PRIMARY KEY,
	product_name TEXT NOT NULL,
	product_category_key INTEGER REFERENCES product_category(product_category_key)
);

-- Các bảng có mối quan hệ với khách hàng
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
    product_category_key INTEGER REFERENCES product_category(product_category_key)
);

CREATE TABLE delivery_location (
	location_code TEXT NOT NULL,
	location_address TEXT,
	system_key INTEGER REFERENCES customer_system(system_key),
	customer_code TEXT REFERENCES customer(customer_code),

    -- Một location_code có thể gồm nhiều customer_code, mỗi cặp trên không thể trùng nhau
    PRIMARY KEY (location_code, location_address)
);

-- Các bảng liên quan tới chương trình khuyến mãi, giá, giảm giá
CREATE TABLE promo_type (
	promo_type_key INTEGER PRIMARY KEY,
	promo_type_name TEXT UNIQUE
);

CREATE TABLE base_price (
	barcode TEXT,
	product_code TEXT REFERENCES product(product_code),
	base_price NUMERIC
);

CREATE TABLE promotion_detail (
	post_name TEXT NOT NULL,
	start_date DATE NOT NULL,
	end_date DATE NOT NULL,
    discount_percentage NUMERIC,
    system_key INTEGER REFERENCES customer_system(system_key),
	promo_type_key INTEGER REFERENCES promo_type(promo_type_key),
    promo_product_code TEXT REFERENCES product(product_code),
	barcode TEXT NOT NULL REFERENCES base_price(barcode)
);

CREATE TABLE cost_center (
    cost_center_code TEXT PRIMARY KEY,
    cost_center_name TEXT UNIQUE,
    branch_key INT REFERENCES branch (branch_key),
    product_category_key INT REFERENCES product_category (product_category_key)
);

CREATE TABLE stg_transactions (
    order_no TEXT,
    order_code TEXT,
    provider_code TEXT,
    location_code TEXT,
    location_name TEXT,
    location_address TEXT,
    buyer TEXT,
    product_order TEXT,
    product_code TEXT,
    product_name TEX,
    barcode TEXT,
    winmart_price NUMERIC,
    product_quantity NUMERIC,
    order_date DATE,
    demand_date DATE
);

CREATE INDEX idx_promo_date ON promotion_detail(start_date, end_date);
CREATE INDEX idx_loc_stg ON stg_transactions(location_code);
CREATE INDEX idx_barcode_stg ON stg_transactions(barcode);
CREATE INDEX idx_date_stg ON stg_transactions(order_date);

CREATE TABLE transactions (
    order_no TEXT,
    order_code TEXT,
    provider_code TEXT,
    location_code TEXT REFERENCES delivery_location(location_code),
    location_name TEXT,
    location_address TEXT,
    buyer TEXT,
    product_order TEXT,
    barcode TEXT REFERENCES base_price(barcode),
    product_code TEXT,
    product_name TEXT,
    winmart_price NUMERIC,
    product_quantity NUMERIC,
    order_date DATE,
    demand_date DATE
);
