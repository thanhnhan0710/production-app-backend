from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from fastapi import HTTPException

# Import Models
from app.models.bom_header import BOMHeader
from app.models.bom_detail import BOMDetail
from app.models.product import Product

# Import Schemas
from app.schemas.bom_schema import BOMHeaderCreate, BOMHeaderUpdate, BOMDetailCreate

class BOMService:
    
    @staticmethod
    def _execute_bom_calculations(header_data, details_list):
        """
        Hàm nội bộ: Tính toán lại toàn bộ định mức dệt (Logic Excel)
        """
        calculated_details = []
        total_actual_cal = 0.0

        # --- Vòng lặp 1: Tính toán sơ bộ ---
        for d in details_list:
            # 1. Chuẩn bị dữ liệu từ Input (hỗ trợ cả Pydantic object và Dict)
            if isinstance(d, BOMDetailCreate):
                d_data = d.model_dump()
                dtex = float(d.yarn_dtex) # Lấy từ computed_field của Pydantic
            else:
                d_data = dict(d)
                # Tự tính dtex nếu input là dict thuần
                try:
                    dtex = float(d_data.get('yarn_type_name', '')[:5])
                except:
                    dtex = 0.0
            
            # Lấy các thông số
            threads = d_data.get('threads', 0)
            twisted = d_data.get('twisted', 1.0)
            crossweave = d_data.get('crossweave_rate', 0.0)
            actual_len = d_data.get('actual_length_cm', 0.0)

            # 2. Áp dụng công thức Excel
            # Formula: Weight Theoretical
            weight_theoretical = ((threads * dtex * twisted * (1 + crossweave)) / 10000) * \
                                 (1 + header_data.total_scrap_rate) * (1 + header_data.total_shrinkage_rate)

            # Formula: Actual Calculation (Hệ số 11000)
            actual_cal = (actual_len / 100) * (dtex / 11000) * threads
            total_actual_cal += actual_cal

            # Lưu tạm vào list
            calculated_details.append({
                "raw_data": d_data, # Dữ liệu gốc đã dump ra dict
                "yarn_dtex": dtex,
                "weight_per_yarn_gm": weight_theoretical,
                "actual_weight_cal": actual_cal
            })

        # --- Vòng lặp 2: Tính tỷ trọng (%) và Finalize ---
        final_details = []
        for item in calculated_details:
            # Tính %
            percentage = item["actual_weight_cal"] / total_actual_cal if total_actual_cal > 0 else 0
            # Tính BOM g/m
            bom_gm = percentage * header_data.target_weight_gm * (1 + header_data.total_scrap_rate)

            # --- QUAN TRỌNG: Xử lý dữ liệu trước khi tạo Model ---
            detail_dict = item["raw_data"].copy()
            
            # Xóa các trường computed/trùng lặp để tránh lỗi "multiple values for keyword argument"
            # Vì chúng ta sẽ truyền các giá trị này thủ công ở bên dưới
            keys_to_remove = ['yarn_dtex', 'weight_per_yarn_gm', 'actual_weight_cal', 'weight_percentage', 'bom_gm']
            for k in keys_to_remove:
                detail_dict.pop(k, None)

            # Nếu thiếu material_id (do import excel), gán tạm = 1 (hoặc xử lý logic tìm material ở đây)
            if 'material_id' not in detail_dict or detail_dict['material_id'] is None:
                detail_dict['material_id'] = 1 

            # Tạo Object BOMDetail
            detail_obj = BOMDetail(
                **detail_dict, # Bung các trường còn lại (threads, yarn_type_name, component_type...)
                
                # Gán các giá trị đã tính toán chính xác
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
        # 1. Kiểm tra sản phẩm
        product = db.query(Product).filter(Product.product_id == bom_in.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {bom_in.product_id} not found")

        # 2. Tạo Header
        db_header = BOMHeader(
            product_id=bom_in.product_id,
            bom_code=bom_in.bom_code,
            bom_name=bom_in.bom_name,
            target_weight_gm=bom_in.target_weight_gm,
            total_scrap_rate=bom_in.total_scrap_rate,
            total_shrinkage_rate=bom_in.total_shrinkage_rate,
            width_behind_loom=bom_in.width_behind_loom,
            picks=bom_in.picks
        )
        
        # 3. Tính toán và gắn Details
        # Lưu ý: Pass db_header vào để lấy scrap/shrinkage rate
        db_header.bom_details = BOMService._execute_bom_calculations(db_header, bom_in.details)
        
        # 4. Lưu DB
        db.add(db_header)
        db.commit()
        db.refresh(db_header)
        return db_header

    @staticmethod
    def update_bom(db: Session, bom_id: int, bom_update: BOMHeaderUpdate):
        db_bom = db.query(BOMHeader).filter(BOMHeader.bom_id == bom_id).first()
        if not db_bom:
            raise HTTPException(status_code=404, detail="BOM not found")

        # 1. Cập nhật Header
        update_data = bom_update.model_dump(exclude_unset=True)
        details_data = update_data.pop('details', None) # Tách details ra xử lý riêng

        for key, value in update_data.items():
            setattr(db_bom, key, value)

        # 2. Xử lý Details (Nếu có gửi kèm)
        if details_data is not None:
            # Xóa sạch chi tiết cũ
            db.query(BOMDetail).filter(BOMDetail.bom_id == bom_id).delete()
            
            # Tính toán lại chi tiết mới dựa trên Header ĐÃ CẬP NHẬT
            new_details = BOMService._execute_bom_calculations(db_bom, bom_update.details)
            
            # Gán vào header (SQLAlchemy sẽ tự lo việc Insert)
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
    def search_boms(db: Session, product_code: str = None, bom_code: str = None, is_active: bool = None):
        query = db.query(BOMHeader).join(Product)

        if product_code:
            query = query.filter(Product.item_code.ilike(f"%{product_code}%")) # Lưu ý: Model Product dùng item_code hay product_code? Kiểm tra lại Model Product
        
        if bom_code:
            query = query.filter(BOMHeader.bom_code.ilike(f"%{bom_code}%"))
            
        if is_active is not None:
            query = query.filter(BOMHeader.is_active == is_active)

        return query.options(joinedload(BOMHeader.bom_details)).all()