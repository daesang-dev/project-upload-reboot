ORDER_CONFIG = {
    "order_index": {
        "keywords": ["STT"],
        "dtype": "string",
        "use": True
    },
    "order_code": {
        "keywords": ["Mã đơn hàng"],
        "dtype": "string",
        "use": True,
    },
    "region": {"keywords": ["Miền"], "dtype": "string", "use": False},
    "province": {
        "keywords": ["Tỉnh"],
        "dtype": "string",
        "use": False,
    },
    "provider_code": {
        "keywords": ["Mã NCC (Site nguồn)"],
        "dtype": "string",
        "use": True,
    },
    "provider_name": {
        "keywords": ["Tên NCC"],
        "dtype": "string",
        "use": False,
    },
    "provider_address": {
        "keywords": ["Địa chỉ NCC"],
        "dtype": "string",
        "use": False,
    },
    "subrange_code": {
        "keywords": ["Mã Sub Range"],
        "dtype": "string",
        "use": False,
    },
    "subrange_name": {
        "keywords": ["Tên Sub Range"],
        "dtype": "string",
        "use": False,
    },
    "location_code": {
        "keywords": ["Mã điểm giao"],
        "dtype": "string",
        "use": True,
    },
    "location_name": {
        "keywords": ["Tên điểm giao"],
        "dtype": "string",
        "use": True,
    },
    "location_address": {
        "keywords": ["Địa chỉ điểm giao"],
        "dtype": "string",
        "use": True,
    },
    "buyer": {
        "keywords": ["Người đặt hàng"],
        "dtype": "string",
        "use": True,
    },
    "product_order": {
        "keywords": ["STT sản phẩm"],
        "dtype": "string",
        "use": True,
    },
    "product_code": {
        "keywords": ["Mã hàng"],
        "dtype": "string",
        "use": False,
    },
    "product_name": {
        "keywords": ["Tên hàng"],
        "dtype": "string",
        "use": True,
    },
    "barcode": {
        "keywords": ["Mã Barcode hàng hóa"],
        "dtype": "string",
        "use": True,
    },
    "uom": {
        "keywords": ["ĐVT"],
        "dtype": "string",
        "use": False,
    },
    "winmart_price": {
        "keywords": ["Đơn giá"],
        "dtype": "decimal",
        "use": True,
    },
    "product_quantity": {
        "keywords": ["Số lượng đặt hàng"],
        "dtype": "decimal",
        "use": True,
    },
    "weight": {
        "keywords": ["Trọng lượng (KG)"],
        "dtype": "decimal",
        "use": False,
    },
    "promised_quantity": {
        "keywords": ["Số lượng hẹn giao hàng"],
        "dtype": "decimal",
        "use": False,
    },
    "shipped_quantity": {
        "keywords": ["SL NCC đã giao"],
        "dtype": "decimal",
        "use": False,
    },
    "actual_quantity": {
        "keywords": ["Số lượng thực tế giao hàng"],
        "dtype": "decimal",
        "use": False,
    },
    "order_date": {
        "keywords": ["Ngày đặt hàng"],
        "dtype": "date",
        "use": True
    },
    "demand_date": {
        "keywords": ["Ngày yêu cầu giao hàng"],
        "dtype": "date",
        "use": True,
    },
    "promised_date": {
        "keywords": ["Ngày NCC hẹn giao hàng"],
        "use": False,
    },
    "promised_time_slot": {
        "keywords": ["Khung giờ hẹn giao hàng"],
        "use": False,
    },
    "confirm_date": {
        "keywords": ["Ngày xác nhận giao hàng"],
        "use": False,
    },
    "confirm_time_slot": {
        "keywords": ["Khung giờ xác nhận giao hàng"],
        "use": False,
    },
    "delivery_date": {
        "keywords": ["Ngày giao hàng"],
        "use": False,
    },
    "supplier_confirm_date": {
        "keywords": ["Ngày NCC xác nhận đã giao"],
        "use": False,
    },
    "extension_date": {
        "keywords": ["Ngày gia hạn"],
        "use": False,
    },
    "status": {
        "keywords": ["Trạng thái"],
        "dtype": "string",
        "use": False,
    },
    "updated_at": {
        "keywords": ["Ngày cập nhật"],
        "use": False,
    },
    "note_1": {
        "keywords": ["Chú thích 1"],
        "dtype": "string",
        "use": False,
    },
    "note_2": {
        "keywords": ["Chú thích 2"],
        "dtype": "string",
        "use": False,
    },
}

INPUT_CONFIG = {
    "stg_product": {
        "sheet_name": "Sản phẩm",
        "conf": {
            "Mã sản phẩm": {"rename": "product_code"},
            "Tên sản phẩm": {"rename": "product_name"},
            "MSG - DS - NK - ĐV": {"rename": "product_category_name"},
            "DS - ĐV": {"rename": "product_brand_name"}
        }
    },
    "stg_base_price": {
        "sheet_name": "Giá gốc",
        "conf": {
            "Mã Barcode": {"rename": "barcode"},
            "Mã sản phẩm": {"rename": "product_code"},
            "Giá gốc": {"rename": "base_price", "dtype": "decimal"},
            "Hệ thống": {"rename": "system_name"}
        }
    },
    "stg_promotion_detail": {
        "sheet_name": "Chương trình khuyến mãi",
        "conf": {
            "Tên chương trình": {"rename": "post_name"},
            "Hệ thống": {"rename": "system_name"},
            "Phạm vi": {"rename": "promo_scope"},
            "Ngày áp dụng": {"rename": "start_date", "dtype": "date"},
            "Ngày kết thúc": {"rename": "end_date", "dtype": "date"},
            "Barcode": {"rename": "barcode"},
            "% Giảm giá": {"rename": "discount_percentage", "dtype": "decimal"},
            "Chương trình KM": {"rename": "promo_type_name"},
            "Mã hàng tặng": {"rename": "promo_product_code"}
        }
    },
    "stg_delivery_location": {
        "sheet_name": "Thông tin điểm giao",
        "conf": {
            "Mã điểm giao": {"rename": "location_code"},
            "Hệ thống": {"rename": "system_name"},
            "Tên điểm giao": {"rename": "location_name"},
            "Địa chỉ điểm giao": {"rename": "location_address"},
            "Mã khách hàng": {"rename": "customer_code"}
        }
    },
    "stg_customer": {
        "sheet_name": "Khách hàng",
        "conf": {
            "Mã khách hàng": {"rename": "customer_code"},
            "Tên khách hàng": {"rename": "customer_name"},
            "Chi nhánh": {"rename": "branch_name"},
            "Nhóm hàng": {"rename": "product_brand_name"},
            "Mã kho": {"rename": "warehouse_code"}
        }
    },
    "stg_cost_center": {
        "sheet_name": "Cost Center",
        "conf": {
            "Nhóm sản phẩm": {"rename": "product_category_name"},
            "Chi nhánh": {"rename": "branch_name"},
            "Cost center": {"rename": "cost_center_code"},
            "Tên": {"rename": "cost_center_name"}
        }
    }
}
