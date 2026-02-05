from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func  # [QUAN TRỌNG] Thêm func để dùng hàm SUM, MAX
from fastapi import HTTPException

# Import Models
from app.models.bom_header import BOMHeader
from app.models.bom_detail import BOMDetail
from app.models.product import Product

# Import Schemas
from app.schemas.bom_schema import BOMHeaderCreate, BOMHeaderUpdate, BOMDetailCreate

class BOMService:
    
    @staticmethod
    def _execute_bom_calculations(header_data: BOMHeader, details_list: BOMDetail):
        """
        Hàm nội bộ: Tính toán lại toàn bộ định mức dệt (Logic Excel)
        Giữ nguyên logic tính toán, chỉ đảm bảo mapping field đúng.
        """
        calculated_details = []
        total_actual_cal = 0.0

        # --- Vòng lặp 1: Tính toán sơ bộ ---
        for d in details_list:
            # 1. Chuẩn bị dữ liệu từ Input (hỗ trợ cả Pydantic object và Dict)
            if isinstance(d, BOMDetailCreate):
                d_data = d.model_dump()
                dtex = float(d.yarn_dtex) # Lấy từ computed_field
            else:
                d_data = dict(d)
                try:
                    dtex = float(d_data.get('yarn_type_name', '')[:5])
                except:
                    dtex = 0.0
            
            # Lấy các thông số
            threads = d_data.get('threads', 0)
            twisted = d_data.get('twisted', 1.0)
            crossweave = d_data.get('crossweave_rate', 0.0)
            actual_len = d_data.get('actual_length_cm', 0.0)
            
            # --- [FIX LOGIC] Lấy component_type an toàn ---
            raw_type = d_data.get('component_type')
            
            # Kiểm tra nếu là Enum Object (có thuộc tính .value) thì lấy value, ngược lại ép kiểu string
            if hasattr(raw_type, 'value'):
                comp_type = str(raw_type.value)
            else:
                comp_type = str(raw_type) if raw_type else ""
            
            # Chuẩn hóa về chữ in hoa và xóa khoảng trắng thừa để so sánh chính xác
            comp_type = comp_type.upper().strip()
            
            # Lấy thông số từ Header để tính toán
            width_m = header_data.width_behind_loom / 1000.0  # Đổi mm -> m
            picks = header_data.picks

            # 2. Áp dụng công thức Excel
            if comp_type == "FILLING" or "WEFT" in comp_type:
                # === CÔNG THỨC CHO SỢI NGANG (FILLING) ===
                # Logic: (Length_per_pick * Picks * Threads * Twist * Dtex) / 10000
                
                # 1. Tính chiều dài sợi trong 1m dây (Width * Picks * Threads * Twisted)
                length_per_meter_belt = width_m * picks * threads * twisted
                
                # 2. Tính trọng lượng lý thuyết (Weight Theoretical)
                # Công thức: (Length * Dtex) / 10000 * (Scrap) * (Shrinkage)
                weight_theoretical = (length_per_meter_belt * dtex / 10000) * \
                                     (1 + (header_data.total_scrap_rate/100)) * \
                                     (1 + (header_data.total_shrinkage_rate/100))
                                     
                # Filling thường tính Actual giống Theoretical
                actual_cal = weight_theoretical
                
            else:
                # === CÔNG THỨC CHO SỢI DỌC (WARP/BINDER/EDGE...) ===
                # Logic cũ
                weight_theoretical = ((threads * dtex * twisted * (1 + (crossweave/100))) / 10000) * \
                                     (1 + (header_data.total_scrap_rate/100)) * \
                                     (1 + (header_data.total_shrinkage_rate/100))

                # Formula: Actual Calculation (Hệ số 11000)
                actual_cal = (actual_len / 100) * (dtex / 11000) * threads
            
            # --- LOGIC ĐÃ CHỈNH SỬA ---
            # Nếu là Filling 2 lần (hoặc 2nd Filling) thì chia đôi thực tế
            if comp_type == "FILLING" or comp_type == "2ND FILLING":
                actual_cal = actual_cal / 2
                
            total_actual_cal += actual_cal

            # Lưu tạm vào list
            calculated_details.append({
                "raw_data": d_data, 
                "yarn_dtex": dtex,
                "weight_per_yarn_gm": weight_theoretical,
                "actual_weight_cal": actual_cal
            })

        # --- Vòng lặp 2: Tính tỷ trọng (%) và Finalize ---
        final_details = []
        for item in calculated_details:
            
            # Tính %
            percentage = (item["actual_weight_cal"] / total_actual_cal)*100 if total_actual_cal > 0 else 0
            # Tính BOM g/m
            bom_gm = percentage /100 * header_data.target_weight_gm * (1 + header_data.total_scrap_rate/100)

            # Xử lý dữ liệu trước khi tạo Model
            detail_dict = item["raw_data"].copy()
            
            # Xóa các trường computed/trùng lặp
            keys_to_remove = ['yarn_dtex', 'weight_per_yarn_gm', 'actual_weight_cal', 'weight_percentage', 'bom_gm']
            for k in keys_to_remove:
                detail_dict.pop(k, None)

            if 'material_id' not in detail_dict or detail_dict['material_id'] is None:
                detail_dict['material_id'] = 1 

            # Tạo Object BOMDetail
            detail_obj = BOMDetail(
                **detail_dict,
                yarn_dtex=item["yarn_dtex"],
                weight_per_yarn_gm=round(item["weight_per_yarn_gm"], 4),
                actual_weight_cal=round(item["actual_weight_cal"], 4),
                weight_percentage=round(percentage, 4),
                bom_gm=round(bom_gm, 4)
            )
            final_details.append(detail_obj)
            
        return final_details

    @staticmethod
    def create_bom(db: Session, bom_in: BOMHeaderCreate):
        # 1. Kiểm tra sản phẩm tồn tại
        product = db.query(Product).filter(Product.product_id == bom_in.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {bom_in.product_id} not found")

        # 2. Kiểm tra trùng lặp (Product + Year)
        existing_bom = db.query(BOMHeader).filter(
            BOMHeader.product_id == bom_in.product_id,
            BOMHeader.applicable_year == bom_in.applicable_year
        ).first()

        if existing_bom:
            raise HTTPException(
                status_code=400, 
                detail=f"BOM for Product {product.item_code} in Year {bom_in.applicable_year} already exists."
            )

        # 3. Tạo Header
        db_header = BOMHeader(
            product_id=bom_in.product_id,
            applicable_year=bom_in.applicable_year,
            
            target_weight_gm=bom_in.target_weight_gm,
            total_scrap_rate=bom_in.total_scrap_rate,
            total_shrinkage_rate=bom_in.total_shrinkage_rate,
            width_behind_loom=bom_in.width_behind_loom,
            picks=bom_in.picks
        )
        
        # 4. Tính toán và gắn Details
        db_header.bom_details = BOMService._execute_bom_calculations(db_header, bom_in.details)
        
        # 5. Lưu DB
        db.add(db_header)
        db.commit()
        db.refresh(db_header)
        return db_header

    @staticmethod
    def update_bom(db: Session, bom_id: int, bom_update: BOMHeaderUpdate):
        db_bom = db.query(BOMHeader).filter(BOMHeader.bom_id == bom_id).first()
        if not db_bom:
            raise HTTPException(status_code=404, detail="BOM not found")

        # 1. Validate Unique Year nếu có thay đổi năm
        if bom_update.applicable_year is not None and bom_update.applicable_year != db_bom.applicable_year:
            conflict_bom = db.query(BOMHeader).filter(
                BOMHeader.product_id == db_bom.product_id,
                BOMHeader.applicable_year == bom_update.applicable_year
            ).first()
            
            if conflict_bom:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot update to Year {bom_update.applicable_year}. BOM for this year already exists."
                )

        # 2. Cập nhật Header
        update_data = bom_update.model_dump(exclude_unset=True)
        details_data = update_data.pop('details', None) 

        for key, value in update_data.items():
            setattr(db_bom, key, value)

        # 3. Xử lý Details (Nếu có gửi kèm)
        if details_data is not None:
            # Xóa sạch chi tiết cũ
            db.query(BOMDetail).filter(BOMDetail.bom_id == bom_id).delete()
            
            # Tính toán lại chi tiết mới dựa trên Header ĐÃ CẬP NHẬT
            new_details = BOMService._execute_bom_calculations(db_bom, bom_update.details)
            
            # Gán vào header
            db_bom.bom_details = new_details

        db.commit()
        db.refresh(db_bom)
        return db_bom

    @staticmethod
    def delete_bom(db: Session, bom_id: int):
        db_bom = db.query(BOMHeader).filter(BOMHeader.bom_id == bom_id).first()
        if db_bom:
            db.delete(db_bom)
            db.commit()
            return True
        return False

    @staticmethod
    def search_boms(db: Session, product_code: str = None, year: int = None, is_active: bool = None):
        """
        Tìm kiếm BOM theo Product Code và Năm
        """
        query = db.query(BOMHeader).join(Product)

        if product_code:
            query = query.filter(Product.item_code.ilike(f"%{product_code}%")) 
        
        if year:
            query = query.filter(BOMHeader.applicable_year == year)
            
        if is_active is not None:
            query = query.filter(BOMHeader.is_active == is_active)

        return query.options(joinedload(BOMHeader.bom_details)).all()

    # --- [TÍNH NĂNG MỚI] TÍNH TỔNG SỐ CUỘN ---
    @staticmethod
    def get_bom_material_summary(db: Session, bom_id: int):
        """
        API Support: Trả về danh sách tổng hợp số cuộn sợi cần thiết.
        Logic: Group By Tên sợi (hoặc Material ID) -> Sum(Threads)
        """
        # 1. Truy vấn DB: Group theo yarn_type_name và tính tổng threads
        summary_query = db.query(
            BOMDetail.yarn_type_name.label("material_name"), # Group theo tên sợi
            func.sum(BOMDetail.threads).label("total_rolls"), # Tính tổng số cuộn
            BOMDetail.material_id,                             # Lấy thêm ID để tham chiếu nếu cần
            # Có thể thêm màu sắc hoặc component_type nếu muốn group chi tiết hơn
        ).filter(
            BOMDetail.bom_id == bom_id
        ).group_by(
            BOMDetail.yarn_type_name,
            BOMDetail.material_id
        ).all()

        # 2. Format dữ liệu trả về cho Frontend
        result = []
        for row in summary_query:
            # Chỉ lấy những dòng có số cuộn > 0 và có tên sợi
            if row.total_rolls and row.total_rolls > 0 and row.material_name:
                result.append({
                    "material_id": row.material_id,
                    "material_name": row.material_name, # VD: 03300-PES-WEISS
                    "total_rolls": int(row.total_rolls) # VD: 348
                })
        
        # Sắp xếp theo tên sợi cho dễ nhìn
        result.sort(key=lambda x: x['material_name'])
        
        return result