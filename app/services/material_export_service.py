from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc
from fastapi import HTTPException
from typing import List, Optional
from datetime import datetime

# Models
from app.models.material_export import MaterialExport, MaterialExportDetail
from app.models.material_inventory import MaterialInventory
from app.models.machine_product_history import MachineProductHistory

# Schemas
from app.schemas.material_export_schema import (
    MaterialExportCreate, 
    MaterialExportUpdate
)

class MaterialExportService:
    def __init__(self, db: Session):
        self.db = db

    def generate_next_export_code(self) -> str:
        now = datetime.now()
        prefix = now.strftime("%Y%m")
        last_export = self.db.query(MaterialExport)\
            .filter(MaterialExport.export_code.like(f"{prefix}-%"))\
            .order_by(desc(MaterialExport.export_code))\
            .first()
            
        if not last_export:
            return f"{prefix}-0001"
        try:
            last_code = last_export.export_code
            parts = last_code.split('-')
            last_seq = int(parts[1]) 
            new_seq = last_seq + 1 
            return f"{prefix}-{new_seq:04d}"
        except (IndexError, ValueError):
            return f"{prefix}-0001"

    def get(self, export_id: int) -> Optional[MaterialExport]:
        return self.db.query(MaterialExport)\
            .options(joinedload(MaterialExport.details).joinedload(MaterialExportDetail.loom))\
            .filter(MaterialExport.id == export_id).first()

    def get_multi(self, skip: int = 0, limit: int = 100, **kwargs):
        query = self.db.query(MaterialExport).options(
            joinedload(MaterialExport.warehouse),
            joinedload(MaterialExport.exporter),
            joinedload(MaterialExport.receiver)
        )
        
        if kwargs.get('warehouse_id'):
            query = query.filter(MaterialExport.warehouse_id == kwargs['warehouse_id'])
        if kwargs.get('exporter_id'):
            query = query.filter(MaterialExport.exporter_id == kwargs['exporter_id'])
        if kwargs.get('receiver_id'):
            query = query.filter(MaterialExport.receiver_id == kwargs['receiver_id'])
        if kwargs.get('from_date'):
            query = query.filter(MaterialExport.export_date >= kwargs['from_date'])
        if kwargs.get('to_date'):
            query = query.filter(MaterialExport.export_date <= kwargs['to_date'])
            
        if kwargs.get('search'):
            term = f"%{kwargs['search']}%"
            query = query.filter(
                or_(
                    MaterialExport.export_code.ilike(term), 
                    MaterialExport.note.ilike(term)
                )
            )
            
        return query.order_by(desc(MaterialExport.export_date)).offset(skip).limit(limit).all()

    # ==========================================
    # [MỚI] HÀM LẤY FULL DỮ LIỆU ĐỂ XUẤT EXCEL
    # ==========================================
    def get_all_for_export_excel(self, **kwargs):
        # Join cực sâu để lấy ra toàn bộ Tên Kho, Người xuất, Tên Vật tư, Tên Máy, Line...
        query = self.db.query(MaterialExport).options(
            joinedload(MaterialExport.warehouse),
            joinedload(MaterialExport.exporter),
            joinedload(MaterialExport.receiver),
            joinedload(MaterialExport.details).joinedload(MaterialExportDetail.material),
            joinedload(MaterialExport.details).joinedload(MaterialExportDetail.batch),
            joinedload(MaterialExport.details).joinedload(MaterialExportDetail.loom).joinedload(MachineProductHistory.machine),
            joinedload(MaterialExport.details).joinedload(MaterialExportDetail.loom).joinedload(MachineProductHistory.product)
        )
        
        if kwargs.get('warehouse_id'):
            query = query.filter(MaterialExport.warehouse_id == kwargs['warehouse_id'])
        if kwargs.get('exporter_id'):
            query = query.filter(MaterialExport.exporter_id == kwargs['exporter_id'])
        if kwargs.get('receiver_id'):
            query = query.filter(MaterialExport.receiver_id == kwargs['receiver_id'])
        if kwargs.get('from_date'):
            query = query.filter(MaterialExport.export_date >= kwargs['from_date'])
        if kwargs.get('to_date'):
            query = query.filter(MaterialExport.export_date <= kwargs['to_date'])
            
        if kwargs.get('search'):
            term = f"%{kwargs['search']}%"
            query = query.filter(
                or_(
                    MaterialExport.export_code.ilike(term), 
                    MaterialExport.note.ilike(term)
                )
            )
            
        return query.order_by(desc(MaterialExport.export_date)).all()

    # ============================
    # TẠO PHIẾU XUẤT KHO MỚI
    # ============================
    def create_export(self, obj_in: MaterialExportCreate) -> MaterialExport:
        export_code = "AUTO" 
        if not hasattr(obj_in, 'export_code') or not obj_in.export_code or obj_in.export_code.strip().upper() == "AUTO":
            export_code = self.generate_next_export_code()
        else:
            export_code = obj_in.export_code

        existing = self.db.query(MaterialExport).filter(MaterialExport.export_code == export_code).first()
        if existing:
             raise HTTPException(status_code=400, detail=f"Mã phiếu xuất {export_code} đã tồn tại.")

        db_export = MaterialExport(
            export_code=export_code,
            export_date=obj_in.export_date or datetime.now().date(),
            warehouse_id=obj_in.warehouse_id,
            department_id=obj_in.department_id,
            exporter_id=obj_in.exporter_id,
            receiver_id=obj_in.receiver_id,
            shift_id=obj_in.shift_id,
            note=obj_in.note,
        )
        self.db.add(db_export)
        self.db.flush() 

        for detail_in in obj_in.details:
            if detail_in.loom_id:
                loom = self.db.query(MachineProductHistory).filter(MachineProductHistory.id == detail_in.loom_id).first()
                if not loom:
                    raise HTTPException(status_code=404, detail=f"Không tìm thấy phiên chạy máy (Loom ID {detail_in.loom_id})")
                if loom.end_time is not None:
                    raise HTTPException(status_code=400, detail=f"Loom (Line {loom.line_number}) đã kết thúc sản xuất, không thể gán thêm sợi.")

            db_detail = MaterialExportDetail(
                export_id=db_export.id,
                material_id=detail_in.material_id,
                batch_id=detail_in.batch_id,
                quantity_kg=detail_in.quantity_kg,          
                quantity_cones=detail_in.quantity_cones,    
                number_of_pallets=detail_in.number_of_pallets, 
                component_type=detail_in.component_type, 
                loom_id=detail_in.loom_id,                  
                note=detail_in.note
            )
            self.db.add(db_detail)

            inventory = self.db.query(MaterialInventory).filter(
                MaterialInventory.warehouse_id == obj_in.warehouse_id,
                MaterialInventory.material_id == detail_in.material_id,
                MaterialInventory.batch_id == detail_in.batch_id
            ).first()

            if not inventory:
                raise HTTPException(status_code=400, detail=f"Lô {detail_in.batch_id} không có sẵn trong Kho này.")

            if inventory.quantity_kg < detail_in.quantity_kg:
                raise HTTPException(status_code=400, detail=f"Không đủ Kg cho Batch {detail_in.batch_id}. Tồn: {inventory.quantity_kg} kg")
            
            if inventory.quantity_cones < detail_in.quantity_cones:
                raise HTTPException(status_code=400, detail=f"Không đủ cuộn cho Batch {detail_in.batch_id}. Tồn: {inventory.quantity_cones} cuộn")

            inventory.quantity_kg -= detail_in.quantity_kg
            inventory.quantity_cones -= detail_in.quantity_cones
            
            if inventory.number_of_pallets >= detail_in.number_of_pallets:
                inventory.number_of_pallets -= detail_in.number_of_pallets
            else:
                inventory.number_of_pallets = 0

            self.db.add(inventory)

        try:
            self.db.commit()
            self.db.refresh(db_export)
            return db_export 
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Lỗi hệ thống lưu dữ liệu: {str(e)}")

    def update(self, export_id: int, obj_in: MaterialExportUpdate) -> MaterialExport:
        db_obj = self.get(export_id)
        if not db_obj: 
            raise HTTPException(status_code=404, detail="Phiếu không tồn tại")
            
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items(): 
            setattr(db_obj, field, value)
            
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, export_id: int):
        db_obj = self.get(export_id)
        if not db_obj: raise HTTPException(status_code=404, detail="Phiếu không tồn tại")
        
        for detail in db_obj.details:
            inventory = self.db.query(MaterialInventory).filter(
                MaterialInventory.warehouse_id == db_obj.warehouse_id,
                MaterialInventory.material_id == detail.material_id,
                MaterialInventory.batch_id == detail.batch_id
            ).first()

            if inventory:
                inventory.quantity_kg += detail.quantity_kg
                inventory.quantity_cones += detail.quantity_cones
                inventory.number_of_pallets += detail.number_of_pallets
                self.db.add(inventory)
            else:
                new_inv = MaterialInventory(
                    warehouse_id=db_obj.warehouse_id,
                    material_id=detail.material_id,
                    batch_id=detail.batch_id,
                    location="N/A",
                    quantity_kg=detail.quantity_kg,
                    quantity_cones=detail.quantity_cones,
                    number_of_pallets=detail.number_of_pallets
                )
                self.db.add(new_inv)
        
        self.db.delete(db_obj)
        self.db.commit()
        return {"message": "Đã hủy phiếu xuất thành công và hoàn trả tồn kho."}
    
    def get_active_batches_on_machine(self, machine_id: int, product_id: int):
        details = self.db.query(MaterialExportDetail).join(
            MachineProductHistory, MaterialExportDetail.loom_id == MachineProductHistory.id
        ).filter(
            MachineProductHistory.machine_id == machine_id,
            MachineProductHistory.product_id == product_id,
            MachineProductHistory.end_time.is_(None)
        ).all()

        result = []
        for d in details:
            result.append({
                # Bắn ra cả snake_case và camelCase để Flutter auto-map không bị trượt
                "batch_id": d.batch_id,
                "batchId": d.batch_id,
                "component_type": d.component_type,
                "yarn_role": d.component_type,
                "yarnRole": d.component_type,
                "quantity_kg": float(d.quantity_kg) if d.quantity_kg else 0.0,
                "quantityKg": float(d.quantity_kg) if d.quantity_kg else 0.0,
            })
            
        return result