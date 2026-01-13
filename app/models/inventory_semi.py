import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

# --- ENUMS (Định nghĩa các lựa chọn cố định) ---

class ExportReason(str, enum.Enum):
    TO_DYEING = "TO_DYEING"       # Chuyển sang nhuộm
    DIRECT_SALE = "DIRECT_SALE"   # Bán thẳng (bán mộc)
    OTHER = "OTHER"               # Khác

class StockStatus(str, enum.Enum):
    IN_STOCK = "IN_STOCK"         # Đang trong kho
    EXPORTED = "EXPORTED"         # Đã xuất
    PENDING = "PENDING"           # Chờ xử lý


# 1. PHIẾU NHẬP KHO (Import Ticket)

class SemiFinishedImportTicket(Base):
    __tablename__ = "semi_finished_import_tickets"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False) # Mã phiếu nhập
    import_date = Column(DateTime, default=datetime.now, nullable=False) # Ngày nhập
    
    # Người cập nhật/tạo phiếu
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    
    # Quan hệ
    employee = relationship("Employee")
    details = relationship("SemiFinishedImportDetail", back_populates="import_ticket")


class SemiFinishedImportDetail(Base):
    __tablename__ = "semi_finished_import_details"

    id = Column(Integer, primary_key=True, index=True)
    
    # Liên kết phiếu nhập
    import_ticket_id = Column(Integer, ForeignKey("semi_finished_import_tickets.id"), nullable=False)
    
    # Liên kết phiếu rổ dệt (Đây chính là item được nhập kho)
    weaving_ticket_id = Column(Integer, ForeignKey("weaving_basket_tickets.id"), nullable=False)
    
    warehouse_location = Column(String(100), nullable=True) # Vị trí kho (Kệ A, Dãy 2...)
    status = Column(Enum(StockStatus), default=StockStatus.IN_STOCK) # Trạng thái
    note = Column(Text, nullable=True)

    # Quan hệ
    import_ticket = relationship("SemiFinishedImportTicket", back_populates="details")
    weaving_ticket = relationship("WeavingBasketTicket")



# 2. PHIẾU XUẤT KHO (Export Ticket)

class SemiFinishedExportTicket(Base):
    __tablename__ = "semi_finished_export_tickets"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False) # Mã phiếu xuất
    export_date = Column(DateTime, default=datetime.now, nullable=False) # Ngày xuất
    
    # Người xuất
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    
    # Lý do xuất (Dùng Enum để code sạch hơn)
    reason = Column(Enum(ExportReason), default=ExportReason.TO_DYEING, nullable=False)
    
    # Quan hệ
    employee = relationship("Employee")
    details = relationship("SemiFinishedExportDetail", back_populates="export_ticket")


class SemiFinishedExportDetail(Base):
    __tablename__ = "semi_finished_export_details"

    id = Column(Integer, primary_key=True, index=True)
    
    # Liên kết phiếu xuất
    export_ticket_id = Column(Integer, ForeignKey("semi_finished_export_tickets.id"), nullable=False)
    
    # Liên kết phiếu rổ dệt (Item được mang đi)
    weaving_ticket_id = Column(Integer, ForeignKey("weaving_basket_tickets.id"), nullable=False)
    
    status = Column(Enum(StockStatus), default=StockStatus.EXPORTED) # Trạng thái (Đã xuất)
    note = Column(Text, nullable=True)

    # Quan hệ
    export_ticket = relationship("SemiFinishedExportTicket", back_populates="details")
    weaving_ticket = relationship("WeavingBasketTicket")