from sqlalchemy.orm import Session
from app.models.user import User
from app.models.log import Log
from app.models.employee import Employee
from app.models.department import Department
from app.models.work_schedule import WorkSchedule
from app.models.shift import Shift
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import SessionLocal, engine

def init_superuser():
    # [QUAN TRỌNG] Dòng lệnh này sẽ tạo toàn bộ bảng trong Database nếu chưa có
    print("Creating tables in database...")
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    email = "admin@oppermann-group.com"
    password = "admin123"
    
    user = db.query(User).filter(User.email == email).first()
    if user:
        print(f"User {email} already exists.")
        return

    print("Creating superuser...")
    db_user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name="Super Admin",
        is_active=True,
        is_superuser=True,
        role="admin"
    )
    
    db.add(db_user)
    db.commit()
    print(f"Superuser created successfully!")
    print(f"Email: {email}")
    print(f"Password: {password}")
    
    db.close()

if __name__ == "__main__":
    init_superuser()