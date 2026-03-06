from sqlalchemy import Column, Integer, String
from app.db.base_class import Base

class POStatus(Base):
    __tablename__ = "po_statuses"

    status_id = Column(Integer, primary_key=True, index=True)
    
    # Mã trạng thái (VD: Draft, Sent, Confirmed, Partial, Completed, Cancelled)
    status_code = Column(String(50), unique=True, index=True, nullable=False)
    
    # Mô tả trạng thái hiển thị cho người dùng
    description = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<POStatus {self.status_code}>"