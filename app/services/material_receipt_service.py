from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from typing import List, Optional
from datetime import datetime
import io
import openpyxl # Bắt buộc cài đặt thư viện này để ghi file Excel

from app.models.material_receipt import MaterialReceipt
from app.models.material_receipt_detail import MaterialReceiptDetail
from app.models.material_batch import MaterialBatch
from app.models.po_detail import PurchaseOrderDetail
from app.schemas.material_receipt_schema import MaterialReceiptCreate, MaterialReceiptUpdate

from app.services.material_batch_service import material_batch_service
from app.services.material_inventory_service import material_inventory_service

class MaterialReceiptService:
    def count_receipts(self, db: Session) -> int:
        return db.query(MaterialReceipt).count()

    def get_receipt(self, db: Session, receipt_id: int) -> Optional[MaterialReceipt]:
        return db.query(MaterialReceipt).filter(MaterialReceipt.receipt_id == receipt_id).first()

    def get_receipts(
        self, db: Session, skip: int = 0, limit: int = 100,
        search: Optional[str] = None, status: Optional[str] = None,
        warehouse_id: Optional[int] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[MaterialReceipt]:
        query = db.query(MaterialReceipt)
        
        if search:
            query = query.filter(MaterialReceipt.receipt_number.ilike(f"%{search}%"))
        if status:
            query = query.filter(MaterialReceipt.status == status)
        if warehouse_id:
            query = query.filter(MaterialReceipt.warehouse_id == warehouse_id)
        if start_date:
            query = query.filter(MaterialReceipt.created_at >= start_date)
        if end_date:
            query = query.filter(MaterialReceipt.created_at <= end_date)
            
        return query.order_by(MaterialReceipt.created_at.desc()).offset(skip).limit(limit).all()

    # ==========================================
    # TÍNH NĂNG XUẤT EXCEL (ĐÃ CẬP NHẬT LẤY TÊN VÀ XUẤT THEO DÒNG VẬT TƯ)
    # ==========================================
    def export_excel(
        self, db: Session, search: Optional[str] = None, status: Optional[str] = None,
        warehouse_id: Optional[int] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> io.BytesIO:
        
        # Dùng joinedload để tải trước toàn bộ Quan hệ (Kho, PO, Chi tiết, Vật tư) -> Tránh bị lỗi N+1 Query làm chậm DB
        query = db.query(MaterialReceipt).options(
            joinedload(MaterialReceipt.warehouse),
            joinedload(MaterialReceipt.po_header),
            joinedload(MaterialReceipt.details).joinedload(MaterialReceiptDetail.material)
        )
        
        if search: query = query.filter(MaterialReceipt.receipt_number.ilike(f"%{search}%"))
        if status: query = query.filter(MaterialReceipt.status == status)
        if warehouse_id: query = query.filter(MaterialReceipt.warehouse_id == warehouse_id)
        if start_date: query = query.filter(MaterialReceipt.created_at >= start_date)
        if end_date: query = query.filter(MaterialReceipt.created_at <= end_date)
            
        receipts = query.order_by(MaterialReceipt.created_at.desc()).all()

        # Tạo file Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Danh Sach Phieu Nhap"

        # Khai báo Header Excel chi tiết
        headers = [
            "Mã Phiếu", "Ngày Phiếu", "Kho Nhận", "Mã PO", 
            "Mã NVL", "Tên NVL", "Lô NCC", "SL Nhận (Kg)", "SL Nhận (Cuộn)", "Vị Trí Cất",
            "Container", "Seal", "Trạng Thái", "Ghi Chú"
        ]
        ws.append(headers)

        # Định dạng in đậm cho Header
        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True)

        # Ghi dữ liệu
        for r in receipts:
            # 1. Trích xuất Tên Kho (Lấy thuộc tính name hoặc warehouse_name tùy cấu trúc DB của bạn)
            wh_name = str(r.warehouse_id)
            if r.warehouse:
                wh_name = getattr(r.warehouse, 'warehouse_name', getattr(r.warehouse, 'name', str(r.warehouse_id)))
            
            # 2. Trích xuất Mã PO
            po_number = r.po_header.po_number if r.po_header else "N/A"
            status_str = "ĐÃ DUYỆT" if r.status == "Completed" else "BẢN NHÁP"
            date_str = r.receipt_date.strftime("%Y-%m-%d") if r.receipt_date else ""

            # 3. Xuất Excel chi tiết tới từng dòng vật tư
            if not r.details:
                # Nếu phiếu rỗng chưa có vật tư nào
                ws.append([
                    r.receipt_number or "", date_str, wh_name, po_number,
                    "", "", "", 0, 0, "",
                    r.container_no or "", r.seal_no or "", status_str, r.note or ""
                ])
            else:
                for d in r.details:
                    mat_code = d.material.material_code if d.material else str(d.material_id)
                    mat_name = d.material.material_name if d.material else ""
                    
                    ws.append([
                        r.receipt_number or "", date_str, wh_name, po_number,
                        mat_code, mat_name, d.supplier_batch_no or "", 
                        d.received_quantity_kg, d.received_quantity_cones, d.location or "",
                        r.container_no or "", r.seal_no or "", status_str, r.note or ""
                    ])

        # Lưu file vào bộ nhớ đệm
        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream


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
            # Flush NGAY LẬP TỨC để Lô này nằm trong DB -> vòng lặp sau generate_batch_code mới tự động tăng
            db.flush() 

            # Bước 3: Cộng vào kho thực tế (MaterialInventory)
            material_inventory_service.add_stock(
                db=db,
                warehouse_id=receipt.warehouse_id,
                material_id=detail.material_id,
                batch_id=new_batch.batch_id,
                location=detail.location,
                qty_kg=detail.received_quantity_kg,
                qty_cones=detail.received_quantity_cones,
                number_of_pallets=detail.number_of_pallets  # <--- BẠN NHỚ THÊM DÒNG NÀY
            )
            
            # BƯỚC 4: Cập nhật ngược lại số thực nhận cho PO Detail
            if receipt.po_header_id:
                po_detail = db.query(PurchaseOrderDetail).filter(
                    PurchaseOrderDetail.po_id == receipt.po_header_id,
                    PurchaseOrderDetail.material_id == detail.material_id
                ).first()
                
                if po_detail:
                    po_detail.received_quantity += detail.received_quantity_kg
                    po_detail.received_rolls += detail.received_quantity_cones
                    db.add(po_detail) # SQLAlchemy sẽ tự động gom vào Transaction

material_receipt_service = MaterialReceiptService()