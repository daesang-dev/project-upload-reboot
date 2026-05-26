PRAGMA foreign_keys = ON;

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
CREATE TABLE promo_type (
	promo_type_key INTEGER PRIMARY KEY,
	promo_type_name TEXT UNIQUE
);

CREATE TABLE base_price (
	barcode TEXT PRIMARY KEY,
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
    product_name TEXT,
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

-- Tạo view

-- View customers: Bao gồm tất cả những thông tin liên quan đến khách hàng
-- Bảng này bao gồm các thông tin về mã điểm giao, tên hệ thống (Win/Win+), mã kho, chi nhánh
-- Cột branch_name sẽ phục vụ việc lựa chọn Cost Center
CREATE VIEW view_customer AS
SELECT
    dl.location_code,
    cs.system_name,
    dl.location_name,
    dl.location_address,
    c.customer_code,
    c.customer_name,
    w.warehouse_code,
    b.branch_name,
    p.ctg_1,
    p.ctg_2
FROM delivery_location dl
JOIN location_customer lc ON dl.location_code = lc.location_code
JOIN customer c ON lc.customer_code = c.customer_code
JOIN branch b ON c.branch_key = b.branch_key
JOIN product_category p ON c.product_category_key = p.product_category_key
JOIN customer_system cs on dl.system_key = cs.system_key
JOIN warehouse w on c.warehouse_key = w.warehouse_key;

-- View product: Bao gồm những thông tin liên quan đến sản phẩm
-- Bảng này gồm các thông tin về mã barcode, mã sản phẩm nào ứng với barcode đó, phân nhóm của sản phẩm đó
-- Cột product_category sẽ phục vụ việc lựa chọn Cost Center
CREATE VIEW view_promotion AS
WITH promotion_r AS (
    SELECT p.post_name,
           p.start_date,
           p.end_date,
           b.barcode,
           pr.product_code,
           pr.product_name,
           b.base_price,
           p.discount_percentage,
           b.base_price * discount_percentage AS discount_amount,
           promo_type_name,
           cs.system_name,
           ctg_1, -- Phân biệt cost center
           ctg_2  -- Phân biệt mã khách hàng
    FROM promotion_detail p
            JOIN base_price b USING (barcode)
            JOIN product pr USING (product_code)
            JOIN product_category pc USING (product_category_key)
            JOIN customer_system cs USING (system_key)
            JOIN promo_type USING (promo_type_key)
)
SELECT
    post_name,
    start_date,
    end_date,
    barcode,
    product_code,
    product_name,
    base_price,
    discount_percentage,
    discount_amount,
    COALESCE(base_price - discount_amount, base_price) AS daesang_price, -- Đây là giá cuối cùng để so sánh với Winmart
    promo_type_name,
    system_name,
    ctg_1, -- Phân biệt cost center
    ctg_2  -- Phân biệt mã khách hàng
FROM promotion_r;

-- Tạo view báo cáo những barcode chưa map với sản phẩm
CREATE VIEW missing_barcode AS
SELECT DISTINCT
    barcode,
    product_name
FROM stg_transactions stg
    LEFT JOIN base_price bp USING (barcode)
WHERE bp.barcode IS NULL
AND stg.barcode IS NOT NULL;

-- Tạo view báo cáo những mã điểm giao chưa map với mã khách hàng
CREATE VIEW missing_location_code AS
SELECT DISTINCT
    stg.location_code,
    stg.location_name,
    stg.location_address
FROM stg_transactions stg
    LEFT JOIN delivery_location dl USING(location_code)
WHERE dl.location_code IS NULL
AND stg.location_code IS NOT NULL;