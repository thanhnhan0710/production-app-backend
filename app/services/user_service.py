from sqlalchemy.orm import Session
from sqlalchemy import or_  # Cần import thêm or_ để tìm kiếm Tên HOẶC Email
from typing import Optional, List, Tuple

from app.models.user import User
from app.schemas.user_schema import UserCreate, UserUpdate
from app.core.security import get_password_hash

class UserService:
    
    # --- BASIC CRUD ---
    def get_by_id(self, db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    # --- ADVANCED SEARCH & FILTER ---
    def get_users(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100, 
        keyword: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        department_id: Optional[int] = None
    ) -> Tuple[List[User], int]:
        """
        Tìm kiếm nâng cao:
        - keyword: Tìm trong Tên hoặc Email
        - filters: role, is_active, department_id
        - return: (danh sách user, tổng số lượng bản ghi tìm thấy)
        """
        query = db.query(User)

        # 1. Lọc theo từ khóa (Tìm kiếm mờ - LIKE)
        if keyword:
            search_format = f"%{keyword}%"
            # Tìm xem keyword có nằm trong full_name HOẶC email không
            query = query.filter(
                or_(
                    User.full_name.ilike(search_format),
                    User.email.ilike(search_format)
                )
            )

        # 2. Lọc theo Role (chính xác)
        if role:
            query = query.filter(User.role == role)

        # 3. Lọc theo Trạng thái
        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        # 4. Lọc theo Phòng ban
        if department_id:
            query = query.filter(User.department_id == department_id)

        # Tính tổng số bản ghi trước khi phân trang (để FE làm phân trang)
        total = query.count()

        # Áp dụng phân trang
        users = query.offset(skip).limit(limit).all()

        return users, total

    # --- CREATE & UPDATE ---
    def create_user(self, db: Session, user: UserCreate) -> User:
        hashed_password = get_password_hash(user.password)
        
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name,
            phone_number=user.phone_number,
            role=user.role,
            department_id=user.department_id,
            is_active=user.is_active,
            is_superuser=user.is_superuser
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def update_user(self, db: Session, db_user: User, user_update: UserUpdate) -> User:
        update_data = user_update.model_dump(exclude_unset=True)

        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password

        for key, value in update_data.items():
            setattr(db_user, key, value)

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    # --- DELETE METHODS ---
    
    def soft_delete_user(self, db: Session, user_id: int) -> Optional[User]:
        """
        Xóa mềm: Chỉ set is_active = False.
        Dữ liệu vẫn còn trong DB để tra cứu lịch sử.
        Khuyên dùng cách này.
        """
        user = self.get_by_id(db, user_id)
        if user:
            user.is_active = False
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def delete_user(self, db: Session, user_id: int) -> Optional[User]:
        """
        Xóa cứng: Bay màu khỏi Database vĩnh viễn.
        Cẩn thận: Có thể lỗi nếu User này đang dính khóa ngoại (Foreign Key)
        với các bảng khác (ví dụ bảng Orders, Logs).
        """
        user = self.get_by_id(db, user_id)
        if user:
            db.delete(user)
            db.commit()
        return user

user_service = UserService()