-- Các bảng liên quan đến sản phẩm
-- Phân biệt loại hàng Daesang / Đức Việt, dùng để chọn mã khách hàng
CREATE TABLE product_brand (
    product_brand_key INTEGER PRIMARY KEY,
    product_brand_name TEXT NOT NULL
);

-- Phân biệt các nhóm hàng, kết hợp với chi nhánh (branch) để chọn cost_center
CREATE TABLE product_category (
    product_category_key INTEGER PRIMARY KEY,
    product_category_name TEXT NOT NULL,
    product_brand_key INTEGER REFERENCES product_brand(product_brand_key)
);

-- Bảng lưu trữ các mã sản phẩm
CREATE TABLE product (
	product_code TEXT PRIMARY KEY,
	product_name TEXT NOT NULL,
	product_category_key INTEGER REFERENCES product_category(product_category_key)
);

-- Phân biệt chuỗi cửa hàng Winmart / Win+, dùng để phân biệt chương trình khuyến mãi áp dụng cho hệ thống nào
CREATE TABLE customer_system (
	system_key INTEGER PRIMARY KEY,
	system_name TEXT UNIQUE
);

-- Mỗi mã khách hàng tương ứng với một mã kho
CREATE TABLE warehouse (
	warehouse_key INTEGER PRIMARY KEY AUTOINCREMENT,
	warehouse_code TEXT UNIQUE
);

-- Mỗi mã khách hàng tương ứng với một chi nhánh, kết hợp chi nhánh với nhóm hàng (product_category) để tìm ra mã Cost Center
CREATE TABLE branch(
	branch_key INTEGER PRIMARY KEY AUTOINCREMENT,
	branch_name TEXT NOT NULL
);

-- Bảng lưu trữ các mã khách hàng
CREATE TABLE customer(
	customer_code TEXT PRIMARY KEY,
	customer_name TEXT NOT NULL,
	branch_key INTEGER REFERENCES branch(branch_key),
	warehouse_key INTEGER REFERENCES warehouse(warehouse_key),
    product_brand_key INTEGER REFERENCES product_brand(product_brand_key)
);

-- Bảng lưu trữ các mã điểm giao
CREATE TABLE delivery_location (
    location_code TEXT PRIMARY KEY,
    location_name TEXT,
    location_address TEXT,
    system_key INTEGER REFERENCES customer_system(system_key)
);

-- Bảng trung gian giữa delivery_location và customer
-- Một mã điểm giao có thể có mối quan hệ với tối đa 2 mã khách hàng (Đức Việt, Daesang)
CREATE TABLE location_customer (
	location_code TEXT REFERENCES delivery_location(location_code),
	customer_code TEXT REFERENCES customer(customer_code),
    UNIQUE (location_code, customer_code)
);

-- Các bảng liên quan tới chương trình khuyến mãi, giá, giảm giá
-- Phân biệt loại khuyến mãi tặng hàng (Mua 1 tặng 1 / Mua 2 tặng 1)
CREATE TABLE promotion_type (
	promo_type_key INTEGER PRIMARY KEY,
	promo_type_name TEXT UNIQUE
);

-- Bảng lưu trữ mã barcode
-- Một mã barcode tại một thời điểm sẽ chỉ có một giá bán, áp dụng cho tất cả các loại chuỗi cửa hàng của Winmart
-- Bảng này không có SCD, dữ liệu giá cũ sẽ bị người dùng thay thế hoàn toàn nếu có giá mới
CREATE TABLE base_price (
	barcode TEXT PRIMARY KEY,
	product_code TEXT REFERENCES product(product_code),
	base_price NUMERIC NOT NULL
);

-- Bảng này lưu trữ chương trình khuyến mãi chi tiết
-- Các chương trình khuyến mãi được gán theo barcode, điều kiện lọc là ngày bắt đầu (start_date), kết thúc (end_date) và hệ thống chuỗi (system_key)
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

-- Tạo index cho bảng promotions_detail để join nhanh
CREATE INDEX idx_promo_date ON promotion_detail(start_date, end_date);
CREATE INDEX idx_loc_stg ON stg_transactions(location_code);
CREATE INDEX idx_barcode_stg ON stg_transactions(barcode);
CREATE INDEX idx_date_stg ON stg_transactions(order_date);

-- Liên kết với bảng Chi nhánh (branch) và Nhóm sản phẩm (product_category)
CREATE TABLE cost_center (
    cost_center_code TEXT PRIMARY KEY,
    cost_center_name TEXT UNIQUE,
    branch_key INT REFERENCES branch (branch_key),
    product_category_key INT REFERENCES product_category (product_category_key)
);

-- Lưu trữ thông tin đơn hàng
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