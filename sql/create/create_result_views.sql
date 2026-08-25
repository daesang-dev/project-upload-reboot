-- Tạo view data sau khi enrich (chưa thêm sản phẩm khuyến mãi)
CREATE VIEW view_data_enrich AS
WITH temp AS (
    SELECT
        t.order_index,
        t.order_code,
        t.provider_code,
        t.location_code,
        t.location_name,
        cs.system_name,
        t.location_address,
        c.customer_code,
        c.customer_name,
        b.branch_name,
        w.warehouse_code,
        t.barcode,
        bp.product_code,
        bp.base_price,
        pd.discount_percentage,
        ROUND(bp.base_price - bp.base_price * coalesce(pd.discount_percentage, 0)) AS daesang_price,
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
        JOIN customer_system cs ON dl.system_key = cs.system_key
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
        system_name,
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
        cost_center_code,
        cost_center_name
FROM temp;


-- View kết quả: Loại bỏ các đơn hàng có tổng giá trị < 500.000vnđ và hiệu số giữa giá winmart và daesang > 2vnđ
CREATE VIEW view_data_result AS
WITH filter_price AS (
    SELECT
        order_index,
        order_code,
        provider_code,
        location_code,
        location_name,
        system_name,
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
        cost_center_code,
        cost_center_name,
        SUM(product_quantity * daesang_price) OVER(PARTITION BY order_code) AS total_order_value
    FROM view_data_enrich
    WHERE price_diff <= 2
    AND product_quantity > 0
),
-- Kiểm tra điều kiện MOQ >= 500000vnđ sau khi đã lọc các sản phẩm sai giá
filter_moq AS (
    SELECT
        *
    FROM filter_price
    WHERE total_order_value >= 000000
),
-- Dựa vào các sản phẩm hợp lệ sau khi lọc MOQ để tạo các dòng sản phẩm tặng kèm
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
         product_order,
         NULL AS barcode,
         'P' AS sell_type_name,
         promo_product_code AS product_code,
         promo_product_name AS product_name,
         CASE
             WHEN promo_type_name = 'Mua 1 tặng 1' THEN product_quantity
             WHEN promo_type_name = 'Mua 2 tặng 1' THEN CAST(ROUND(product_quantity / 2.0) AS INT)
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
     FROM filter_moq
     WHERE promo_product_code IS NOT NULL
 ),
 merged AS (
     SELECT
         order_index, order_code, provider_code, location_code, location_name, location_address, customer_code, customer_name,
         branch_name, warehouse_code, buyer, product_order, barcode, sell_type_name, product_code, product_name, product_quantity, promo_product_code, promo_product_name,
         promo_type_name, source_product_code, order_date, base_price, discount_percentage, daesang_price, winmart_price,
         price_diff, total_order_value, cost_center_code, cost_center_name
     FROM filter_moq
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


-- Tạo view báo cáo những sản phẩm sai giá
CREATE VIEW view_failed_price AS
WITH failed_price AS (
    SELECT DISTINCT
        order_code,
        barcode,
        system_name,
        product_code,
        product_name,
        base_price,
        discount_percentage,
        daesang_price,
        winmart_price,
        price_diff
    FROM view_data_enrich
    WHERE price_diff > 2
    OR product_quantity <= 0
)
SELECT * FROM failed_price;


-- Tạo view báo cáo những đơn hàng không đủ MOQ sau khi lọc các sản phẩm sai giá
CREATE VIEW view_failed_moq AS
WITH temp AS (
	SELECT 
	vde.*,
	SUM(vde.product_quantity * vde.daesang_price) OVER(PARTITION BY vde.order_code) AS total_order_value
	FROM view_data_enrich vde
	LEFT JOIN view_failed_price vfp 
	ON vde.order_code = vfp.order_code
	AND vde.product_code = vfp.product_code
	WHERE vfp.product_code IS NULL
)
SELECT * FROM temp
WHERE total_order_value < 000000;


-- Tạo sheet Header của template upload SAP
CREATE VIEW view_upload_header AS
SELECT DISTINCT
    head AS "Document Key",
    customer_code AS "Customer",
    2 AS "Business Place",
    strftime('%d%m%Y', DATE('now')) AS "Posting Date(ddmmyyyy)",
    strftime('%d%m%Y', DATE('now')) AS "Due Date(ddmmyyyy)",
    strftime('%d%m%Y', DATE('now')) AS "Document Date(ddmmyyyy)",
    NULL AS "Sales Employee",
    1 AS "Order Type",
    "S01" AS "Sales Type",
    NULL AS "Team Code",
    NULL AS "Branch Code",
    order_code AS "Remarks",
    NULL AS "Journal Remark",
    order_code AS "Customer Ref. No.",
    NULL AS "Customer Ref. No.1",
    location_code AS "AddressCode"
FROM view_data_result;


-- Tạo view Line của template upload SAP
CREATE VIEW view_upload_line AS
SELECT DISTINCT
    head AS "Document Key",
    line AS "Row",
    sell_type_name AS "Selling Type",
    product_code AS "Item No.",
    NULL AS "Unit of Measure",
    product_quantity AS "UOM Qty",
    winmart_price AS "Unit Price",
    NULL AS "Discount %",
    "A8" AS "Tax Code",
    warehouse_code AS "Whse",
    cost_center_code AS "Distr. Rule",
    NULL AS "G/L Account",
    NULL AS "COGS Account",
    source_product_code AS "Source Item"
FROM view_data_result;