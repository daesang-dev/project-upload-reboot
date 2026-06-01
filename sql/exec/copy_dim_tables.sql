-- Import các sản phẩm
INSERT INTO product_brand (product_brand_name)
SELECT DISTINCT
    product_brand_name
FROM stg_product;

INSERT INTO product_category(product_category_name, product_brand_key)
WITH temp AS (
    SELECT DISTINCT
        product_category_name,
        product_brand_name
    FROM stg_product
)
SELECT
    t.product_category_name,
    product_brand_key
FROM temp t
LEFT JOIN product_brand pb USING (product_brand_name);

INSERT INTO product
SELECT
    product_code,
    product_name,
    product_category_key
FROM stg_product p
LEFT JOIN product_category USING(product_category_name);

INSERT INTO base_price
SELECT DISTINCT
    barcode,
    product_code,
    base_price
FROM stg_base_price;

INSERT INTO branch(branch_name) -- Bỏ qua key tự tăng
SELECT DISTINCT
    branch_name
FROM stg_customer;

INSERT INTO warehouse(warehouse_code) -- Bỏ qua key tự tăng
SELECT DISTINCT
    warehouse_code
FROM stg_customer;

INSERT INTO location_customer
SELECT DISTINCT
    location_code,
    customer_code
FROM stg_delivery_location;

INSERT INTO customer_system(system_name)
SELECT DISTINCT
    system_name
FROM stg_delivery_location;

INSERT INTO delivery_location(location_code, location_name, location_address, system_key)
WITH location_r AS (
    SELECT DISTINCT
        location_code,
        system_name
    FROM stg_delivery_location
)
SELECT
    r.location_code,
    l.location_name,
    l.location_address,
    cs.system_key
FROM location_r r
     LEFT JOIN customer_system cs USING (system_name)
     LEFT JOIN stg_delivery_location l ON r.location_code = l.location_code;

INSERT INTO promotion_type (promo_type_name)
SELECT DISTINCT
    promo_type_name
FROM stg_promotion_detail
WHERE promo_type_name IS NOT NULL;

INSERT INTO promotion_detail
SELECT
    post_name,
    start_date,
    end_date,
    discount_percentage,
    system_key,
    promo_type_key,
    promo_product_code,
    barcode
FROM stg_promotion_detail spd
LEFT JOIN customer_system cs ON spd.system_name = "Toàn bộ" OR spd.system_name = cs.system_name
LEFT JOIN promotion_type pt ON spd.promo_type_name = pt.promo_type_name;

INSERT INTO cost_center
SELECT
    cost_center_code,
    cost_center_name,
    branch_key,
    product_category_key
FROM stg_cost_center scc
     JOIN product_category pc ON scc.product_category_name = pc.product_category_name
     JOIN branch b ON scc.branch_name = b.branch_name;

INSERT INTO customer
SELECT
    customer_code,
    customer_name,
    branch_key,
    warehouse_key,
    product_brand_key
FROM stg_customer sc
JOIN branch b ON sc.branch_name = b.branch_name
JOIN product_brand pb ON sc.product_brand_name = pb.product_brand_name
JOIN warehouse w ON sc.warehouse_code = w.warehouse_code