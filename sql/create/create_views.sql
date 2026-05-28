-- View customers: Bao gồm tất cả những thông tin liên quan đến khách hàng
-- Bảng này bao gồm các thông tin về mã điểm giao, tên hệ thống (Win/Win+), mã kho, chi nhánh
-- Cột branch_name sẽ phục vụ việc lựa chọn Cost Center
CREATE VIEW view_location AS
SELECT
    dl.location_code,
    cs.system_name,
    dl.location_name,
    dl.location_address,
    c.customer_code,
    c.customer_name,
    w.warehouse_code,
    b.branch_name,
    pb.product_brand_name
FROM delivery_location dl
    JOIN location_customer lc ON dl.location_code = lc.location_code
    JOIN customer c ON lc.customer_code = c.customer_code
    JOIN branch b ON c.branch_key = b.branch_key
    JOIN product_brand pb ON c.product_brand_key = pb.product_brand_key
    JOIN customer_system cs on dl.system_key = cs.system_key
    JOIN warehouse w on c.warehouse_key = w.warehouse_key;


-- View product: Bao gồm những thông tin liên quan đến sản phẩm
-- Bảng này gồm các thông tin về mã barcode, mã sản phẩm nào ứng với barcode đó, phân nhóm của sản phẩm đó
-- Cột product_category sẽ phục vụ việc lựa chọn Cost Center
CREATE VIEW view_promotion AS
WITH temp AS (
    SELECT
        pd.barcode,
        bp.product_code,
        p.product_name,
        pc.product_category_name,
        pb.product_brand_name,
        pd.post_name,
        pd.start_date,
        pd.end_date,
        bp.base_price,
        pd.discount_percentage,
        bp.base_price - (bp.base_price * COALESCE(pd.discount_percentage, 0)) AS discounted_price,
        pt.promo_type_name,
        pd.promo_product_code,
        p2.product_name AS promo_product_name,
        cs.system_name
    FROM promotion_detail pd
             JOIN base_price bp ON pd.barcode = bp.barcode
             LEFT JOIN customer_system cs ON pd.system_key = cs.system_key OR cs.system_key IS NULL
             LEFT JOIN product p ON bp.product_code = p.product_code
             LEFT JOIN product p2 ON pd.promo_product_code = p2.product_code
             LEFT JOIN product_category pc ON p.product_category_key = pc.product_category_key
             LEFT JOIN product_brand pb ON pc.product_brand_key = pb.product_brand_key
             LEFT JOIN promotion_type pt ON pd.promo_type_key = pt.promo_type_key
)
SELECT
    barcode,
    product_code,
    product_name,
    product_category_name,
    product_brand_name,
    post_name,
    start_date,
    end_date,
    base_price,
    discount_percentage,
    discounted_price AS daesang_price,
    promo_type_name,
    promo_product_code,
    promo_product_name,
    system_name
FROM temp
;

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


-- Tạo view data sau khi enrich (chưa thêm sản phẩm khuyến mãi)
CREATE VIEW view_data_enrich AS
WITH temp AS (
    SELECT
        t.order_index,
        t.order_code,
        t.provider_code,
        t.location_code,
        t.location_name,
        t.location_address,
        c.customer_code,
        c.customer_name,
        b.branch_name,
        w.warehouse_code,
        t.barcode,
        bp.product_code,
        bp.base_price,
        pd.discount_percentage,
        bp.base_price - bp.base_price * coalesce(pd.discount_percentage, 0) AS daesang_price,
        pb_cust.product_brand_name AS customer_brand_name, -- Nhóm sản phẩm của Khách hàng
        t.buyer,
        t.product_order,
        t.product_name,
        t.winmart_price,
        t.product_quantity,
        pd.promo_product_code,
        p2.product_name AS promo_product_name,
        pt.promo_type_name,
        t.order_date,
        cost_center_code,
        cost_center_name
    FROM transactions t
        -- Bước 1: Lấy thông tin sản phẩm và ngành hàng/nhãn hàng của Sản Phẩm trong giao dịch trước
        LEFT JOIN base_price bp ON t.barcode = bp.barcode
        LEFT JOIN product p ON bp.product_code = p.product_code
        LEFT JOIN product_category pc ON p.product_category_key = pc.product_category_key
        -- pb_prod là nhãn hàng (Brand) của chính cái sản phẩm vừa mua
        LEFT JOIN product_brand pb_prod ON pc.product_brand_key = pb_prod.product_brand_key

        -- Bước 2: Từ điểm giao, tìm Khách hàng thỏa mãn: Phải cùng điểm giao VÀ Khách hàng đó phải quản lý Nhãn hàng của sản phẩm
        JOIN delivery_location dl ON t.location_code = dl.location_code
        JOIN location_customer lc ON dl.location_code = lc.location_code
        JOIN customer c ON lc.customer_code = c.customer_code
        -- LỌC CHÍNH TẠI ĐÂY: Chỉ chọn khách hàng có brand_key khớp với brand_key của sản phẩm
        AND c.product_brand_key = pc.product_brand_key

        JOIN branch b ON c.branch_key = b.branch_key
        JOIN warehouse w ON c.warehouse_key = w.warehouse_key
        -- pb_cust là nhãn hàng hiển thị thông tin của Khách hàng
        LEFT JOIN product_brand pb_cust ON c.product_brand_key = pb_cust.product_brand_key

        -- Bước 3: LEFT JOIN lấy khuyến mãi (Khớp Barcode + Đúng chuỗi lấy từ điểm giao + Khung thời gian)
        LEFT JOIN promotion_detail pd
            ON t.barcode = pd.barcode
            AND dl.system_key = pd.system_key
            AND t.order_date BETWEEN pd.start_date AND pd.end_date

        LEFT JOIN product p2 ON pd.promo_product_code = p2.product_code

        LEFT JOIN promotion_type pt ON pd.promo_type_key = pt.promo_type_key

        -- Bước 4: JOIN cost_center dựa vào branch_key và product_category_key để xác định cost_center_code
        LEFT JOIN cost_center cc
            ON b.branch_key = cc.branch_key
            AND pc.product_category_key = cc.product_category_key
    )
    SELECT
        order_index,
        order_code,
        provider_code,
        location_code,
        location_name,
        location_address,
        customer_code,
        customer_name,
        branch_name,
        warehouse_code,
        buyer,
        product_order,
        barcode,
        product_code,
        product_name,
        product_quantity,
        promo_product_code,
        promo_product_name,
        promo_type_name,
        order_date,
        base_price,
        discount_percentage,
        daesang_price,
        winmart_price,
        ABS(daesang_price - winmart_price) AS price_diff,
        SUM(product_quantity * daesang_price) OVER(PARTITION BY order_code) AS total_order_value,
        cost_center_code,
        cost_center_name
FROM temp;


CREATE VIEW failed_data_moq AS
WITH failed_moq AS (
   SELECT
       *
   FROM view_data_enrich
   WHERE total_order_value < 500000
)
SELECT * FROM failed_moq;


CREATE VIEW failed_data_price AS
WITH failed_price AS (
    SELECT
        *
    FROM view_data_enrich
    WHERE price_diff > 2
)
SELECT * FROM failed_price;


CREATE VIEW view_data_merge AS
WITH sales AS (
    SELECT
        order_index,
        order_code,
        provider_code,
        location_code,
        location_name,
        location_address,
        customer_code,
        customer_name,
        branch_name,
        warehouse_code,
        buyer,
        CAST(product_order AS INTEGER) AS product_order,
        barcode,
        'S' AS sell_type_name,
        product_code,
        product_name,
        product_quantity,
        promo_product_code,
        promo_product_name,
        promo_type_name,
        NULL AS source_product_code,
        order_date,
        base_price,
        discount_percentage,
        daesang_price,
        winmart_price,
        price_diff,
        total_order_value,
        cost_center_code,
        cost_center_name
    FROM view_data_enrich
    WHERE total_order_value > 500000
      AND price_diff <= 2
),
promotions AS (
    SELECT
         order_index,
         order_code,
         provider_code,
         location_code,
         location_name,
         location_address,
         customer_code,
         customer_name,
         branch_name,
         warehouse_code,
         buyer,
         product_order, -- Cột này tự động kế thừa kiểu INTEGER từ bảng sales
         NULL AS barcode,
         'P' AS sell_type_name,
         promo_product_code AS product_code,
         promo_product_name AS product_name,
         CASE
             WHEN promo_type_name = 'Mua 1 tặng 1' THEN product_quantity
             WHEN promo_type_name = 'Mua 2 tặng 1' THEN CAST(ROUND(product_quantity / 2.0) AS INT)
             ELSE NULL
             END AS product_quantity,
         promo_product_code,
         promo_product_name,
         promo_type_name,
         product_code AS source_product_code,
         order_date,
         NULL AS base_price,
         NULL AS discount_percentage,
         NULL AS daesang_price,
         NULL AS winmart_price,
         NULL AS price_diff,
         total_order_value,
         cost_center_code,
         cost_center_name
     FROM sales
     WHERE promo_product_code IS NOT NULL
 ),
 merged AS (
     SELECT
         order_index, order_code, provider_code, location_code, location_name, location_address, customer_code, customer_name, branch_name, warehouse_code, buyer, product_order, barcode, sell_type_name, product_code, product_name, product_quantity, promo_product_code, promo_product_name,
         promo_type_name, source_product_code, order_date, base_price, discount_percentage, daesang_price, winmart_price,
         price_diff, total_order_value, cost_center_code, cost_center_name
     FROM sales

     UNION ALL

     SELECT
         order_index, order_code, provider_code, location_code, location_name, location_address, customer_code, customer_name, branch_name, warehouse_code, buyer, product_order, barcode, sell_type_name, product_code, product_name, product_quantity,
         NULL AS promo_product_code,
         NULL AS promo_product_name,
         NULL AS promo_type_name,
         source_product_code,
         order_date, base_price, discount_percentage, daesang_price, winmart_price,
         price_diff, total_order_value, cost_center_code, cost_center_name
     FROM promotions
 ),
result AS (
    SELECT * FROM merged
    ORDER BY order_code, product_order, sell_type_name DESC, order_index
)
SELECT
    dense_rank() over (ORDER BY order_code) AS head,
    row_number() over (PARTITION BY order_code) AS line,
    *
FROM result
LIMIT -1;