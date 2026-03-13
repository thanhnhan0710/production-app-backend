# app/schemas/weaving_production_analytics_schema.py

from pydantic import BaseModel
from typing import List, Optional


# ─────────────────────────────────────────
# Sản lượng theo Máy
# ─────────────────────────────────────────
class ProductionByMachineItem(BaseModel):
    """Một điểm dữ liệu: (kỳ, máy, line) → sản lượng"""
    period_label: str          # Nhãn trục X: "Ca A", "01/01", "Tuần 2", ...
    period_order: int          # Số thứ tự để sắp xếp trục X
    machine_id: int
    machine_name: str
    line: int
    total_weight: float        # Sản lượng (kg)
    run_waste: float           # Phế run (kg)
    setup_waste: float         # Phế setup (kg)
    total_waste: float         # Tổng phế = run_waste + setup_waste


class ProductionByMachineResponse(BaseModel):
    period: str                        # "shift" | "day" | "week" | "month" | "year"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    items: List[ProductionByMachineItem]


# ─────────────────────────────────────────
# Sản lượng theo Mã sản phẩm
# ─────────────────────────────────────────
class ProductionByProductItem(BaseModel):
    """Một điểm dữ liệu: (kỳ, mã SP) → sản lượng"""
    period_label: str
    period_order: int
    item_code: str             # Mã sản phẩm (6622076...)
    total_weight: float        # Sản lượng (kg)


class ProductionByProductResponse(BaseModel):
    period: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    items: List[ProductionByProductItem]


# ─────────────────────────────────────────
# KPI Tổng quan (cho cards trên dashboard)
# ─────────────────────────────────────────
class ProductionKPIResponse(BaseModel):
    period: str
    total_weight: float
    total_run_waste: float
    total_setup_waste: float
    total_waste: float
    waste_rate_pct: float          # % phế / (sản lượng + phế) × 100
    record_count: int