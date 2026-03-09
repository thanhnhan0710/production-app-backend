from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Optional
from datetime import datetime

from app.models.material_receipt import MaterialReceipt
from app.models.material_receipt_detail import MaterialReceiptDetail
from app.models.material_batch import MaterialBatch
from app.schemas.material_receipt_schema import MaterialReceiptCreate, MaterialReceiptUpdate

# Import các Service khác để gọi logic nghiệp vụ
from app.services.material_batch_service import material_batch_service
from app.services.material_inventory_service import material_inventory_service

class MaterialReceiptService:
    def count_receipts(self, db: Session) -> int:
        """Đếm tổng số phiếu nhập kho"""
        return db.query(MaterialReceipt).count()

    def get_receipt(self, db: Session, receipt_id: int) -> Optional[MaterialReceipt]:
        return db.query(MaterialReceipt).filter(MaterialReceipt.receipt_id == receipt_id).first()

    def get_receipts(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        warehouse_id: Optional[int] = None
    ) -> List[MaterialReceipt]:
        query = db.query(MaterialReceipt)
        
        if search:
            # Tìm kiếm theo mã phiếu nhập
            query = query.filter(MaterialReceipt.receipt_number.ilike(f"%{search}%"))
        if status:
            query = query.filter(MaterialReceipt.status == status)
        if warehouse_id:
            query = query.filter(MaterialReceipt.warehouse_id == warehouse_id)
            
        return query.order_by(MaterialReceipt.created_at.desc()).offset(skip).limit(limit).all()

    # ==========================================
    # LOGIC TẠO PHIẾU NHẬP
    # ==========================================
    def create_receipt(self, db: Session, obj_in: MaterialReceiptCreate) -> MaterialReceipt:
        # 1. Tách phần thông tin phiếu (Header)
        receipt_data = obj_in.model_dump(exclude={"details"})
        
        # Nếu không gửi mã phiếu nhập, hệ thống tự sinh mã (VD: RC202603091020)
        if not receipt_data.get("receipt_number"):
            receipt_data["receipt_number"] = f"RC{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
        db_receipt = MaterialReceipt(**receipt_data)
        db.add(db_receipt)
        db.flush() # Đẩy vào DB tạm để lấy receipt_id

        # 2. Tạo các dòng chi tiết (Details)
        for detail_in in obj_in.details:
            db_detail = MaterialReceiptDetail(
                **detail_in.model_dump(), 
                receipt_id=db_receipt.receipt_id
            )
            db.add(db_detail)
        db.flush() # Đẩy details vào DB tạm để lấy detail_id

        # 3. NẾU NGƯỜI DÙNG TẠO PHIẾU Ở TRẠNG THÁI "Completed" NGAY TỪ ĐẦU -> GỌI LOGIC TẠO LÔ VÀ TỒN KHO
        if db_receipt.status == "Completed":
            self._process_inventory_and_batch(db, db_receipt)

        # 4. Lưu chính thức toàn bộ quá trình (Transaction Commit)
        db.commit()
        db.refresh(db_receipt)
        return db_receipt

    # ==========================================
    # LOGIC SỬA PHIẾU NHẬP (DUYỆT PHIẾU)
    # ==========================================
    def update_receipt(self, db: Session, receipt_id: int, obj_in: MaterialReceiptUpdate) -> MaterialReceipt:
        db_receipt = self.get_receipt(db, receipt_id)
        if not db_receipt:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiếu nhập")

        # RÀNG BUỘC KẾ TOÁN: Không cho phép sửa phiếu đã Hoàn thành
        if db_receipt.status == "Completed":
            raise HTTPException(status_code=400, detail="Phiếu nhập đã hoàn thành và cộng tồn kho, không thể chỉnh sửa!")

        update_data = obj_in.model_dump(exclude_unset=True, exclude={"details"})
        
        # Kiểm tra xem có phải thao tác duyệt phiếu không (Chuyển status -> Completed)
        is_completing = False
        if "status" in update_data and update_data["status"] == "Completed" and db_receipt.status != "Completed":
            is_completing = True

        # Cập nhật Header
        for field, value in update_data.items():
            setattr(db_receipt, field, value)

        # NẾU DUYỆT PHIẾU -> GỌI LOGIC TẠO LÔ VÀ TỒN KHO
        if is_completing:
            self._process_inventory_and_batch(db, db_receipt)

        db.commit()
        db.refresh(db_receipt)
        return db_receipt

    def delete_receipt(self, db: Session, receipt_id: int) -> bool:
        db_receipt = self.get_receipt(db, receipt_id)
        if not db_receipt:
            return False
            
        if db_receipt.status == "Completed":
            raise HTTPException(status_code=400, detail="Không thể xóa phiếu nhập đã cộng tồn kho!")
            
        db.delete(db_receipt)
        db.commit()
        return True

    # ==========================================
    # LOGIC CỐT LÕI: SINH MÃ LÔ VÀ TĂNG TỒN KHO
    # ==========================================
    def _process_inventory_and_batch(self, db: Session, receipt: MaterialReceipt):
        # Duyệt qua từng dòng hàng hóa nhập vào
        for detail in receipt.details:
            # Bước 1: Sinh mã lô nội bộ tự động (V260001...)
            batch_code = material_batch_service.generate_batch_code(db)
            
            # Bước 2: Lưu thông tin định danh Lô (MaterialBatch)
            new_batch = MaterialBatch(
                batch_code=batch_code,
                material_id=detail.material_id,
                receipt_detail_id=detail.detail_id,
                supplier_batch_no=detail.supplier_batch_no,
                origin_country=detail.origin_country,
                initial_quantity_kg=detail.received_quantity_kg,
                initial_quantity_cones=detail.received_quantity_cones,
                status="Available"
            )
            db.add(new_batch)
            # Flush NGAY LẬP TỨC để Lô này nằm trong DB -> vòng lặp sau generate_batch_code mới tự động tăng lên V260002
            db.flush() 

            # Bước 3: Cộng vào kho thực tế (MaterialInventory)
            material_inventory_service.add_stock(
                db=db,
                warehouse_id=receipt.warehouse_id,
                material_id=detail.material_id,
                batch_id=new_batch.batch_id,
                location=detail.location,
                qty_kg=detail.received_quantity_kg,
                qty_cones=detail.received_quantity_cones
            )

material_receipt_service = MaterialReceiptService()