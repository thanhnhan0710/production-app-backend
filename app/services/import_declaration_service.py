from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from fastapi import HTTPException
from typing import List, Optional
from datetime import date

from app.models.import_declaration import ImportDeclaration, ImportDeclarationDetail, ImportType
from app.schemas.import_declaration_schema import (
    ImportDeclarationCreate, 
    ImportDeclarationUpdate, 
    ImportDetailCreate,
    ImportDetailUpdate # Cần thêm schema này trong file schema
)

class ImportDeclarationService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id: int) -> Optional[ImportDeclaration]:
        return self.db.query(ImportDeclaration).options(
            joinedload(ImportDeclaration.details).joinedload(ImportDeclarationDetail.material)
        ).filter(ImportDeclaration.id == id).first()

    def get_by_no(self, declaration_no: str) -> Optional[ImportDeclaration]:
        return self.db.query(ImportDeclaration).filter(ImportDeclaration.declaration_no == declaration_no).first()

    def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        search: str = None,
        import_type: ImportType = None,
        from_date: date = None,
        to_date: date = None
    ) -> List[ImportDeclaration]:
        query = self.db.query(ImportDeclaration)

        if import_type:
            query = query.filter(ImportDeclaration.type_of_import == import_type)

        if from_date:
            query = query.filter(ImportDeclaration.declaration_date >= from_date)
        
        if to_date:
            query = query.filter(ImportDeclaration.declaration_date <= to_date)

        if search:
            search_filter = or_(
                ImportDeclaration.declaration_no.ilike(f"%{search}%"),
                ImportDeclaration.bill_of_lading.ilike(f"%{search}%"),
                ImportDeclaration.invoice_no.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        return query.order_by(ImportDeclaration.declaration_date.desc()).offset(skip).limit(limit).all()

    def create(self, obj_in: ImportDeclarationCreate) -> ImportDeclaration:
        if self.get_by_no(obj_in.declaration_no):
            raise HTTPException(status_code=400, detail=f"Số tờ khai {obj_in.declaration_no} đã tồn tại.")

        db_obj = ImportDeclaration(
            declaration_no=obj_in.declaration_no,
            declaration_date=obj_in.declaration_date,
            type_of_import=obj_in.type_of_import,
            bill_of_lading=obj_in.bill_of_lading,
            invoice_no=obj_in.invoice_no,
            total_tax_amount=obj_in.total_tax_amount,
            note=obj_in.note
        )
        self.db.add(db_obj)
        self.db.flush()

        if obj_in.details:
            for detail in obj_in.details:
                db_detail = ImportDeclarationDetail(
                    declaration_id=db_obj.id,
                    material_id=detail.material_id,
                    po_detail_id=detail.po_detail_id,
                    quantity=detail.quantity,
                    unit_price=detail.unit_price,
                    hs_code_actual=detail.hs_code_actual
                )
                self.db.add(db_detail)
        
        self.db.commit()
        return self.get(db_obj.id)

    def update(self, db_obj: ImportDeclaration, obj_in: ImportDeclarationUpdate) -> ImportDeclaration:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        self.db.commit()
        return self.get(db_obj.id)

    # --- [MỚI] Xóa Tờ khai ---
    def delete(self, id: int) -> bool:
        obj = self.get(id)
        if not obj:
            raise HTTPException(status_code=404, detail="Tờ khai không tồn tại.")
        self.db.delete(obj)
        self.db.commit()
        return True

    # --- [MỚI] Chi tiết hàng hóa ---
    def add_detail(self, declaration_id: int, detail_in: ImportDetailCreate) -> ImportDeclarationDetail:
        decl = self.get(declaration_id)
        if not decl:
            raise HTTPException(status_code=404, detail="Tờ khai không tồn tại.")

        db_detail = ImportDeclarationDetail(
            declaration_id=declaration_id,
            material_id=detail_in.material_id,
            po_detail_id=detail_in.po_detail_id,
            quantity=detail_in.quantity,
            unit_price=detail_in.unit_price,
            hs_code_actual=detail_in.hs_code_actual
        )
        self.db.add(db_detail)
        self.db.commit()
        self.db.refresh(db_detail)
        return db_detail

    def update_detail(self, detail_id: int, detail_in: ImportDetailUpdate) -> ImportDeclarationDetail:
        db_detail = self.db.query(ImportDeclarationDetail).filter(ImportDeclarationDetail.detail_id == detail_id).first()
        if not db_detail:
            raise HTTPException(status_code=404, detail="Chi tiết không tồn tại.")

        update_data = detail_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_detail, field, value)
            
        self.db.add(db_detail)
        self.db.commit()
        self.db.refresh(db_detail)
        return db_detail

    def delete_detail(self, detail_id: int) -> bool:
        db_detail = self.db.query(ImportDeclarationDetail).filter(ImportDeclarationDetail.detail_id == detail_id).first()
        if not db_detail:
            raise HTTPException(status_code=404, detail="Chi tiết không tồn tại.")
            
        self.db.delete(db_detail)
        self.db.commit()
        return True