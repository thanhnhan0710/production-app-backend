from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Material(Base):
    __tablename__ = "materials"

    material_id = Column(Integer, primary_key=True, index=True)
    material_name = Column(String(150), nullable=False)

    lot_code = Column(String(50), nullable=True)
    import_date = Column(Date, nullable=False)

    quantity = Column(Integer, nullable=False)

    unit_id = Column(Integer, ForeignKey("units.unit_id"))
    imported_by = Column(Integer, ForeignKey("employees.employee_id"))

    note= Column(String(150), nullable=True)

    unit = relationship("Unit", back_populates="materials")

    # Quan hệ n-1: Người nhập vật tư là một nhân viên
    importer = relationship("Employee")
