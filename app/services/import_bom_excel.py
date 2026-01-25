import pandas as pd
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.models.product import Product
from app.services.bom_service import BOMService
from app.schemas.bom_schema import BOMHeaderCreate, BOMDetailCreate
from app.models.bom_detail import BOMComponentType
from app.db.base import Base

def import_bom_from_excel(file_path: str):
    db: Session = SessionLocal()
    try:
        # Đọc tất cả các sheet (sheet_name=None trả về dict {sheet_name: dataframe})
        excel_data = pd.read_excel(file_path, sheet_name=None, header=None)

        for sheet_name, df in excel_data.items():
            print(f"--- Đang xử lý sản phẩm: {sheet_name} ---")

            # 1. Kiểm tra hoặc tạo Product
            product = db.query(Product).filter(Product.item_code == sheet_name).first()
            if not product:
                product = Product(item_code=sheet_name, note=f"Imported from {sheet_name}")
                db.add(product)
                db.commit()
                db.refresh(product)

            # 2. Thu thập thông số Header (Dựa trên tọa độ ô trong ảnh)
            # Lưu ý: pandas index bắt đầu từ 0 (Hàng 1 -> index 0, Cột A -> index 0)
            target_weight = df.iloc[2, 10]  # Ô K3 (Row 3, Col K)
            scrap_rate = df.iloc[17, 5]     # Ô F18 (Row 18, Col F)
            shrinkage_rate = df.iloc[18, 5] # Ô F19 (Row 19, Col F)

            # 3. Duyệt danh sách sợi (Dòng 5 đến 17)
            bom_details = []
            # Bắt đầu từ hàng index 4 (Dòng 5 thực tế)
            for i in range(4, 17):
                comp_name = str(df.iloc[i, 0]).strip() # Cột A: Loại (Ground, Binder...)
                threads = df.iloc[i, 1]                # Cột B: Threads
                yarn_type = df.iloc[i, 3]               # Cột D: Type (Mã sợi)
                
                # Chỉ xử lý nếu có số lượng sợi > 0 và có mã sợi
                if pd.notna(threads) and threads > 0 and pd.notna(yarn_type):
                    # Mapping tên từ Excel sang Enum của chúng ta
                    comp_type = map_excel_to_enum(comp_name)
                    
                    detail = BOMDetailCreate(
                        component_type=comp_type,
                        threads=int(threads),
                        yarn_type_name=str(yarn_type),
                        twisted=float(df.iloc[i, 4]) if pd.notna(df.iloc[i, 4]) else 1.0, # Cột E
                        crossweave_rate=float(df.iloc[i, 5]) if pd.notna(df.iloc[i, 5]) else 0.0, # Cột F
                        actual_length_cm=float(df.iloc[i, 7]) if pd.notna(df.iloc[i, 7]) else 0.0 # Cột H
                    )
                    bom_details.append(detail)

            # 4. Gọi Service để tính toán và lưu vào DB
            bom_in = BOMHeaderCreate(
                product_id=product.product_id,
                bom_code=f"BOM-{sheet_name}-AUTO",
                bom_name=f"BOM tự động import cho {sheet_name}",
                target_weight_gm=float(target_weight) if pd.notna(target_weight) else 0.0,
                total_scrap_rate=float(scrap_rate) if pd.notna(scrap_rate) else 0.0,
                total_shrinkage_rate=float(shrinkage_rate) if pd.notna(shrinkage_rate) else 0.0,
                details=bom_details
            )

            BOMService.create_bom(db, bom_in)
            print(f"Thành công: Đã import BOM cho {sheet_name}")

    except Exception as e:
        print(f"Lỗi khi import: {e}")
        db.rollback()
    finally:
        db.close()

def map_excel_to_enum(excel_name: str) -> BOMComponentType:
    """Hàm chuyển đổi tên tiếng Anh trong Excel sang Enum của Backend"""
    mapping = {
        "Ground": BOMComponentType.GROUND,
        "Grd. Marker": BOMComponentType.GRD_MARKER,
        "Edge": BOMComponentType.EDGE,
        "Binder": BOMComponentType.BINDER,
        "Stuffer": BOMComponentType.STUFFER,
        "Catch cord": BOMComponentType.CATCH_CORD,
        "Filling": BOMComponentType.FILLING,
        "2nd Filling": BOMComponentType.SECOND_FILLING
    }
    return mapping.get(excel_name, BOMComponentType.GROUND)

if __name__ == "__main__":
    import_bom_from_excel("/app/static/BOM YARN 2025.xlsm")