from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
from app.models.log import Log
from app.schemas.log_schema import LogCreate

class LogService:
    def create_log(
        self,
        db: Session,
        user_id: Optional[int],
        action: str,
        target_type: str = None,
        target_id: int = None,
        description: str = None,
        changes: Dict[str, Any] = None, # Truyền dict vào, SQLAlchemy tự ép sang JSON
        ip_address: str = None
    ):
        """
        Hàm dùng chung để ghi log hệ thống.
        """
        try:
            db_log = Log(
                user_id=user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                description=description,
                changes=changes,
                ip_address=ip_address
            )
            db.add(db_log)
            db.commit()
            db.refresh(db_log)
            return db_log
        except Exception as e:
            # Nếu log lỗi, không được làm crash luồng chính
            print(f"LỖI GHI LOG: {e}")
            db.rollback()
            return None

    def get_logs(self, db: Session, skip: int = 0, limit: int = 100, user_id: int = None):
        query = db.query(Log)
        if user_id:
            query = query.filter(Log.user_id == user_id)
        # Sắp xếp mới nhất lên đầu
        return query.order_by(Log.timestamp.desc()).offset(skip).limit(limit).all()

log_service = LogService()