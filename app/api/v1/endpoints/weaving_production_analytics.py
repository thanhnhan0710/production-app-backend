# app/api/v1/endpoints/weaving_production_analytics.py

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import io

from app.api import deps
from app.schemas.weaving_production_analytics_schema import (
    ProductionByMachineResponse,
    ProductionByProductResponse,
    ProductionKPIResponse,
)
from app.services.weaving_production_analytics_service import (
    WeavingProductionAnalyticsService,
)

router = APIRouter()

PERIOD_CHOICES = ["shift", "day", "week", "month", "year"]


# ─────────────────────────────────────────
# GET KPI (Tổng quan nhanh)
# ─────────────────────────────────────────
@router.get("/kpi", response_model=ProductionKPIResponse)
def get_production_kpi(
    period: str = Query("day", enum=PERIOD_CHOICES),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(deps.get_db),
):
    """Lấy KPI tổng quan: tổng sản lượng, tổng phế, tỷ lệ phế trong kỳ."""
    svc = WeavingProductionAnalyticsService(db)
    return svc.get_kpi(period, start_date, end_date)


# ─────────────────────────────────────────
# GET Sản lượng theo Máy
# ─────────────────────────────────────────
@router.get("/by-machine", response_model=ProductionByMachineResponse)
def get_production_by_machine(
    period: str = Query("day", enum=PERIOD_CHOICES),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(deps.get_db),
):
    """
    Sản lượng & phế theo từng máy, nhóm theo kỳ.
    Dùng để vẽ biểu đồ cột trên Dashboard.
    """
    svc = WeavingProductionAnalyticsService(db)
    return svc.get_by_machine(period, start_date, end_date)


# ─────────────────────────────────────────
# GET Sản lượng theo Mã sản phẩm
# ─────────────────────────────────────────
@router.get("/by-product", response_model=ProductionByProductResponse)
def get_production_by_product(
    period: str = Query("day", enum=PERIOD_CHOICES),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(deps.get_db),
):
    """
    Sản lượng theo mã sản phẩm (item_code từ phiếu rổ dệt), nhóm theo kỳ.
    Yêu cầu WeavingProduction.weaving_ticket_id được điền đúng.
    """
    svc = WeavingProductionAnalyticsService(db)
    return svc.get_by_product(period, start_date, end_date)


# ─────────────────────────────────────────
# GET Xuất Excel
# ─────────────────────────────────────────
@router.get("/export-excel")
def export_excel(
    period: str = Query("day", enum=PERIOD_CHOICES),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    export_type: str = Query(
        "all",
        enum=["by_machine", "by_product", "waste", "all"],
        description="Loại xuất: by_machine / by_product / waste / all",
    ),
    db: Session = Depends(deps.get_db),
):
    """
    Xuất file Excel sản lượng.
    - by_machine  → Sheet "Sản lượng theo máy"
    - waste       → Sheet "Phế theo máy"
    - by_product  → Sheet "Sản lượng theo mã SP"
    - all         → Tất cả 3 sheet
    """
    svc = WeavingProductionAnalyticsService(db)
    excel_bytes = svc.export_excel(period, start_date, end_date, export_type)

    period_vi = {
        "shift": "Ca", "day": "Ngay", "week": "Tuan",
        "month": "Thang", "year": "Nam",
    }.get(period, period)

    from datetime import date as dt_date
    filename = f"SanLuong_{period_vi}_{dt_date.today().strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )