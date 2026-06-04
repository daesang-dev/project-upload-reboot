-- View này chặn những chuơng trình khuyến mãi trùng khoảng thời gian nhưng khác chương trình (giảm giá, tặng hàng)
CREATE VIEW view_overlapped_promotions AS WITH temp AS (
    SELECT
        ROW_NUMBER() OVER() + 1 AS row_id,
        LOWER(TRIM(system_name)) AS temp_system_name,
        *
    FROM stg_promotion_detail
)
SELECT
    *
FROM
    temp t1 LEFT JOIN temp t2 ON t1.barcode = t2.barcode
    AND t1.row_id < t2.row_id
WHERE
    (t1.temp_system_name = t2.temp_system_name OR t1.temp_system_name = 'toàn bộ' OR t2.temp_system_name = 'toàn bộ')
    AND t1.start_date <= t2.end_date
    AND t1.end_date >= t2.start_date
    AND (
        t1.discount_percentage IS DISTINCT FROM t2.discount_percentage
        OR t1.promo_type_name IS DISTINCT FROM t2.promo_type_name
        OR t1.promo_product_code IS DISTINCT FROM t2.promo_product_code
    );


-- View này hiển thị những chương trình khuyến mãi trùng khoảng thời gian và bị trùng lặp nội dung với chương trình khác trước hoặc sau nó
CREATE VIEW view_duplicated_promotions AS
WITH temp AS (
    SELECT
        ROW_NUMBER() OVER() + 1 AS row_id,
        LOWER(TRIM(system_name)) AS temp_system_name,
        *
    FROM stg_promotion_detail
)
SELECT
    *
FROM
    temp t1 LEFT JOIN temp t2 ON t1.barcode = t2.barcode
    AND t1.row_id < t2.row_id
WHERE
    (t1.temp_system_name = t2.temp_system_name OR t1.temp_system_name = 'toàn bộ' OR t2.temp_system_name = 'toàn bộ')
    AND t1.start_date <= t2.end_date
    AND t1.end_date >= t2.start_date
    AND (
        COALESCE(t1.discount_percentage, 0) = COALESCE(t2.discount_percentage, 0)
        AND COALESCE(t1.promo_type_name, '') = COALESCE(t2.promo_type_name, '')
        AND COALESCE(t1.promo_product_code, '') = COALESCE(t2.promo_product_code, '')
    );


-- Tạo view báo cáo những barcode chưa map với sản phẩm
CREATE VIEW view_missing_barcode AS
SELECT DISTINCT
    barcode,
    product_name
FROM stg_transactions stg
         LEFT JOIN base_price bp USING (barcode)
WHERE bp.barcode IS NULL
  AND stg.barcode IS NOT NULL;


-- Tạo view báo cáo những mã điểm giao chưa map với mã khách hàng
CREATE VIEW view_missing_location_code AS
SELECT DISTINCT
    stg.location_code,
    stg.location_name,
    stg.location_address
FROM stg_transactions stg
         LEFT JOIN delivery_location dl USING(location_code)
WHERE dl.location_code IS NULL
  AND stg.location_code IS NOT NULL