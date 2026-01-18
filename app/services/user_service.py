<<<<<<< HEAD
# C:\Users\nhan_\Documents\production-app-backend\app\services\user_service.py
from sqlalchemy.orm import Session, joinedload
=======
from sqlalchemy.orm import Session, joinedload # [MỚI] Import joinedload
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
from sqlalchemy import or_
from typing import Optional, List, Tuple

from app.models.user import User
from app.schemas.user_schema import UserCreate, UserUpdate
from app.core.security import get_password_hash

class UserService:
    
    # --- BASIC CRUD ---
    def get_by_id(self, db: Session, user_id: int) -> Optional[User]:
<<<<<<< HEAD
        # [OPTIONAL] Thêm options(joinedload(User.employee)) nếu muốn lấy info employee khi get detail
        return db.query(User).filter(User.user_id == user_id).first()
=======
        # [SỬA] Thêm options(joinedload(User.employee)) để lấy luôn thông tin nhân viên
        return db.query(User).options(joinedload(User.employee)).filter(User.user_id == user_id).first()
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).options(joinedload(User.employee)).filter(User.email == email).first()

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
    ) -> Tuple[List[User], int]:
<<<<<<< HEAD
        
        query = db.query(User)
=======
        """
        Tìm kiếm nâng cao:
        - keyword: Tìm trong Tên hoặc Email
        - filters: role, is_active
        - return: (danh sách user, tổng số lượng bản ghi tìm thấy)
        """
        
        # [SỬA QUAN TRỌNG] Thêm joinedload để lấy quan hệ employee
        # Nếu không có dòng này, Pydantic schema sẽ không lấy được data 'employee' để trả về FE
        query = db.query(User).options(joinedload(User.employee))
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3

        # 1. Lọc theo từ khóa
        if keyword:
            search_format = f"%{keyword}%"
            query = query.filter(
                or_(
                    User.full_name.ilike(search_format),
                    User.email.ilike(search_format)
                )
            )

        if role:
            query = query.filter(User.role == role)

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

<<<<<<< HEAD
=======
        # Tính tổng số bản ghi
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
        total = query.count()

        # [NEW] Sử dụng joinedload để load luôn thông tin Employee
        # Giúp Frontend có dữ liệu json['employee']['full_name'] ngay lập tức
        users = query.options(joinedload(User.employee)).offset(skip).limit(limit).all()

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
            is_active=user.is_active,
            is_superuser=user.is_superuser,
<<<<<<< HEAD
            # [NEW] Lưu employee_id
            employee_id=user.employee_id
=======
            employee_id=user.employee_id  # [MỚI] Map thêm trường employee_id
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
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

<<<<<<< HEAD
        # Tự động map các field còn lại (bao gồm cả employee_id nếu có)
=======
        # Hàm này tự động map tất cả key trong update_data vào db_user
        # Vì employee_id có trong schema UserUpdate, nó sẽ tự động được cập nhật ở đây
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
        for key, value in update_data.items():
            setattr(db_user, key, value)

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

<<<<<<< HEAD
    # --- DELETE METHODS --- (Giữ nguyên như cũ)
=======
    # --- DELETE METHODS ---
    # (Giữ nguyên như cũ)
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
    def soft_delete_user(self, db: Session, user_id: int) -> Optional[User]:
        user = self.get_by_id(db, user_id)
        if user:
            user.is_active = False
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    def delete_user(self, db: Session, user_id: int) -> Optional[User]:
        user = self.get_by_id(db, user_id)
        if user:
            db.delete(user)
            db.commit()
        return user

user_service = UserService()