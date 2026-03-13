# app/services/weaving_production_analytics_service.py

import io
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, cast, Integer

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.models.weaving_production import WeavingProduction
from app.models.weaving_basket_ticket import WeavingBasketTicket
from app.models.product import Product
from app.schemas.weaving_production_analytics_schema import (
    ProductionByMachineItem,
    ProductionByMachineResponse,
    ProductionByProductItem,
    ProductionByProductResponse,
    ProductionKPIResponse,
)


# ═══════════════════════════════════════════════════════
# HELPER: Tính khoảng ngày mặc định theo period
# ═══════════════════════════════════════════════════════
def _default_date_range(period: str) -> Tuple[date, date]:
    today = date.today()
    if period == "shift":
        return today, today
    elif period == "day":
        # 7 ngày gần nhất
        return today - timedelta(days=6), today
    elif period == "week":
        # 8 tuần gần nhất
        start = today - timedelta(weeks=7)
        return start - timedelta(days=start.weekday()), today
    elif period == "month":
        # 6 tháng gần nhất
        first_day = today.replace(day=1)
        start = (first_day - timedelta(days=1)).replace(day=1)
        for _ in range(5):
            start = (start - timedelta(days=1)).replace(day=1)
        return start, today
    elif period == "year":
        return today.replace(month=1, day=1, year=today.year - 2), today
    return today - timedelta(days=30), today


# ═══════════════════════════════════════════════════════
# HELPER: Tạo nhãn + thứ tự từ datetime theo period
# ═══════════════════════════════════════════════════════
def _make_label(dt, period: str, shift_name: Optional[str] = None) -> Tuple[str, int]:
    # Nếu dt là string (do date_format trả về string), cần xử lý hoặc dựa vào db trả về
    if isinstance(dt, str):
        try:
            # Xử lý nhanh dựa theo độ dài chuỗi trả về từ MySQL
            if period == "day":
                dt_obj = datetime.strptime(dt, "%Y-%m-%d")
                return dt_obj.strftime("%d/%m"), int(dt_obj.strftime("%Y%m%d"))
            elif period == "month":
                dt_obj = datetime.strptime(dt, "%Y-%m")
                return dt_obj.strftime("%m/%Y"), int(dt_obj.strftime("%Y%m"))
            elif period == "year":
                return dt, int(dt)
            elif period == "week":
                # Định dạng %x-%v của MySQL (vd 2026-11)
                return f"Tuần {dt[-2:]}/{dt[:4]}", int(dt.replace("-", ""))
        except Exception:
            return str(dt), 0

    if not isinstance(dt, datetime):
        return str(dt), 0

    if period == "shift":
        label = shift_name or f"Ca {dt.strftime('%H')}"
        order = int(dt.strftime("%H"))
    elif period == "day":
        label = dt.strftime("%d/%m")
        order = int(dt.strftime("%Y%m%d"))
    elif period == "week":
        iso = dt.isocalendar()
        label = f"T{iso[1]}/{dt.year}"
        order = int(f"{dt.year}{iso[1]:02d}")
    elif period == "month":
        label = dt.strftime("%m/%Y")
        order = int(dt.strftime("%Y%m"))
    elif period == "year":
        label = dt.strftime("%Y")
        order = int(dt.strftime("%Y"))
    else:
        label = dt.strftime("%d/%m/%Y")
        order = int(dt.strftime("%Y%m%d"))
    return label, order


# ═══════════════════════════════════════════════════════
# HELPER: SQLAlchemy date truncation expression (ĐÃ SỬA CHO MYSQL)
# ═══════════════════════════════════════════════════════
def _trunc_expr(period: str, col):
    """Trả về expression để group theo period (Dành cho MySQL)."""
    if period == "shift":
        # Group theo ca = theo shift_id
        return col  # Placeholder; ta group theo shift_id riêng
    
    # Mapping các chuỗi định dạng của MySQL (DATE_FORMAT)
    mapping = {
        "day": "%Y-%m-%d",
        "week": "%x-%v",   # Năm - Tuần
        "month": "%Y-%m",
        "year": "%Y",
    }
    fmt = mapping.get(period, "%Y-%m-%d")
    return func.date_format(col, fmt)


class WeavingProductionAnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    # ─────────────────────────────────────────
    # 1. Sản lượng + Phế theo Máy
    # ─────────────────────────────────────────
    def get_by_machine(
        self,
        period: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> ProductionByMachineResponse:
        if not start_date or not end_date:
            start_date, end_date = _default_date_range(period)

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        if period == "shift":
            rows = self._query_by_shift_machine(start_dt, end_dt)
        else:
            rows = self._query_by_period_machine(period, start_dt, end_dt)

        items = []
        for r in rows:
            run_w = float(r.run_waste or 0)
            setup_w = float(r.setup_waste or 0)
            items.append(
                ProductionByMachineItem(
                    period_label=r.period_label,
                    period_order=r.period_order,
                    machine_id=r.machine_id,
                    machine_name=r.machine_name or f"Máy {r.machine_id}",
                    line=r.line,
                    total_weight=float(r.total_weight or 0),
                    run_waste=run_w,
                    setup_waste=setup_w,
                    total_waste=round(run_w + setup_w, 3),
                )
            )

        items.sort(key=lambda x: (x.period_order, x.machine_name, x.line))
        return ProductionByMachineResponse(
            period=period,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            items=items,
        )

    def _query_by_period_machine(self, period: str, start_dt: datetime, end_dt: datetime):
        trunc = _trunc_expr(period, WeavingProduction.updated_at)
        from app.models.machine import WeavingMachine  # local import

        rows = (
            self.db.query(
                trunc.label("period_ts"),
                WeavingProduction.machine_id,
                func.coalesce(WeavingMachine.machine_name, "").label("machine_name"),
                WeavingProduction.line,
                func.sum(WeavingProduction.total_weight).label("total_weight"),
                func.sum(WeavingProduction.run_waste).label("run_waste"),
                func.sum(WeavingProduction.setup_waste).label("setup_waste"),
            )
            .join(WeavingMachine, WeavingMachine.machine_id == WeavingProduction.machine_id, isouter=True)
            .filter(
                WeavingProduction.updated_at >= start_dt,
                WeavingProduction.updated_at <= end_dt,
            )
            .group_by(trunc, WeavingProduction.machine_id, WeavingMachine.machine_name, WeavingProduction.line)
            .order_by(trunc)
            .all()
        )

        result = []
        for r in rows:
            label, order = _make_label(r.period_ts, period)

            class Row:
                pass

            row = Row()
            row.period_label = label
            row.period_order = order
            row.machine_id = r.machine_id
            row.machine_name = r.machine_name
            row.line = r.line
            row.total_weight = r.total_weight
            row.run_waste = r.run_waste
            row.setup_waste = r.setup_waste
            result.append(row)
        return result

    def _query_by_shift_machine(self, start_dt: datetime, end_dt: datetime):
        from app.models.machine import WeavingMachine
        from app.models.shift import Shift

        rows = (
            self.db.query(
                WeavingProduction.shift_id,
                func.coalesce(Shift.shift_name, "Không rõ ca").label("shift_name"),
                WeavingProduction.machine_id,
                func.coalesce(WeavingMachine.machine_name, "").label("machine_name"),
                WeavingProduction.line,
                func.sum(WeavingProduction.total_weight).label("total_weight"),
                func.sum(WeavingProduction.run_waste).label("run_waste"),
                func.sum(WeavingProduction.setup_waste).label("setup_waste"),
            )
            .join(WeavingMachine, WeavingMachine.machine_id == WeavingProduction.machine_id, isouter=True)
            .join(Shift, Shift.shift_id == WeavingProduction.shift_id, isouter=True)
            .filter(
                WeavingProduction.updated_at >= start_dt,
                WeavingProduction.updated_at <= end_dt,
            )
            .group_by(
                WeavingProduction.shift_id,
                Shift.shift_name,
                WeavingProduction.machine_id,
                WeavingMachine.machine_name,
                WeavingProduction.line,
            )
            .all()
        )

        result = []
        for i, r in enumerate(rows):

            class Row:
                pass

            row = Row()
            row.period_label = r.shift_name
            row.period_order = i
            row.machine_id = r.machine_id
            row.machine_name = r.machine_name
            row.line = r.line
            row.total_weight = r.total_weight
            row.run_waste = r.run_waste
            row.setup_waste = r.setup_waste
            result.append(row)
        return result

    # ─────────────────────────────────────────
    # 2. Sản lượng theo Mã sản phẩm
    # ─────────────────────────────────────────
    def get_by_product(
        self,
        period: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> ProductionByProductResponse:
        if not start_date or not end_date:
            start_date, end_date = _default_date_range(period)

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        if period == "shift":
            rows = self._query_by_shift_product(start_dt, end_dt)
        else:
            rows = self._query_by_period_product(period, start_dt, end_dt)

        items = []
        for r in rows:
            items.append(
                ProductionByProductItem(
                    period_label=r.period_label,
                    period_order=r.period_order,
                    item_code=r.item_code or "N/A",
                    total_weight=float(r.total_weight or 0),
                )
            )

        items.sort(key=lambda x: (x.period_order, x.item_code))
        return ProductionByProductResponse(
            period=period,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            items=items,
        )

    def _query_by_period_product(self, period: str, start_dt: datetime, end_dt: datetime):
        trunc = _trunc_expr(period, WeavingProduction.updated_at)

        rows = (
            self.db.query(
                trunc.label("period_ts"),
                func.coalesce(Product.item_code, "N/A").label("item_code"),
                func.sum(WeavingProduction.total_weight).label("total_weight"),
            )
            .join(
                WeavingBasketTicket,
                WeavingBasketTicket.id == WeavingProduction.weaving_ticket_id,
                isouter=True,
            )
            .join(
                Product,
                Product.product_id == WeavingBasketTicket.product_id,
                isouter=True,
            )
            .filter(
                WeavingProduction.updated_at >= start_dt,
                WeavingProduction.updated_at <= end_dt,
            )
            .group_by(trunc, Product.item_code)
            .order_by(trunc)
            .all()
        )

        result = []
        for r in rows:
            label, order = _make_label(r.period_ts, period)

            class Row:
                pass

            row = Row()
            row.period_label = label
            row.period_order = order
            row.item_code = r.item_code
            row.total_weight = r.total_weight
            result.append(row)
        return result

    def _query_by_shift_product(self, start_dt: datetime, end_dt: datetime):
        from app.models.shift import Shift

        rows = (
            self.db.query(
                WeavingProduction.shift_id,
                func.coalesce(Shift.shift_name, "Không rõ ca").label("shift_name"),
                func.coalesce(Product.item_code, "N/A").label("item_code"),
                func.sum(WeavingProduction.total_weight).label("total_weight"),
            )
            .join(Shift, Shift.shift_id == WeavingProduction.shift_id, isouter=True)
            .join(
                WeavingBasketTicket,
                WeavingBasketTicket.id == WeavingProduction.weaving_ticket_id,
                isouter=True,
            )
            .join(
                Product,
                Product.product_id == WeavingBasketTicket.product_id,
                isouter=True,
            )
            .filter(
                WeavingProduction.updated_at >= start_dt,
                WeavingProduction.updated_at <= end_dt,
            )
            .group_by(WeavingProduction.shift_id, Shift.shift_name, Product.item_code)
            .all()
        )

        result = []
        for i, r in enumerate(rows):

            class Row:
                pass

            row = Row()
            row.period_label = r.shift_name
            row.period_order = i
            row.item_code = r.item_code
            row.total_weight = r.total_weight
            result.append(row)
        return result

    # ─────────────────────────────────────────
    # 3. KPI Tổng quan
    # ─────────────────────────────────────────
    def get_kpi(
        self,
        period: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> ProductionKPIResponse:
        if not start_date or not end_date:
            start_date, end_date = _default_date_range(period)

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        row = (
            self.db.query(
                func.coalesce(func.sum(WeavingProduction.total_weight), 0).label("tw"),
                func.coalesce(func.sum(WeavingProduction.run_waste), 0).label("rw"),
                func.coalesce(func.sum(WeavingProduction.setup_waste), 0).label("sw"),
                func.count(WeavingProduction.id).label("cnt"),
            )
            .filter(
                WeavingProduction.updated_at >= start_dt,
                WeavingProduction.updated_at <= end_dt,
            )
            .first()
        )

        tw = float(row.tw)
        rw = float(row.rw)
        sw = float(row.sw)
        total_waste = rw + sw
        waste_rate = round(total_waste / (tw + total_waste) * 100, 2) if (tw + total_waste) > 0 else 0.0

        return ProductionKPIResponse(
            period=period,
            total_weight=round(tw, 2),
            total_run_waste=round(rw, 2),
            total_setup_waste=round(sw, 2),
            total_waste=round(total_waste, 2),
            waste_rate_pct=waste_rate,
            record_count=row.cnt,
        )

    # ─────────────────────────────────────────
    # 4. Xuất Excel
    # ─────────────────────────────────────────
    def export_excel(
        self,
        period: str,
        start_date: Optional[date],
        end_date: Optional[date],
        export_type: str,  # "by_machine" | "by_product" | "waste"
    ) -> bytes:
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # Remove default sheet

        # Lấy dữ liệu
        machine_data = self.get_by_machine(period, start_date, end_date)
        product_data = self.get_by_product(period, start_date, end_date)

        period_vi = {
            "shift": "Ca", "day": "Ngày", "week": "Tuần",
            "month": "Tháng", "year": "Năm"
        }.get(period, period)

        date_range_str = f"{start_date} → {end_date}" if start_date else ""

        if export_type in ("by_machine", "all"):
            self._write_machine_sheet(wb, machine_data.items, period_vi, date_range_str)
        if export_type in ("waste", "all"):
            self._write_waste_sheet(wb, machine_data.items, period_vi, date_range_str)
        if export_type in ("by_product", "all"):
            self._write_product_sheet(wb, product_data.items, period_vi, date_range_str)

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    # ──────────────────── EXCEL HELPERS ────────────────────

    _HEADER_FILL = PatternFill("solid", fgColor="003366")
    _HEADER_FONT = Font(color="FFFFFF", bold=True, size=11)
    _ALT_FILL = PatternFill("solid", fgColor="EBF0FA")
    _BORDER = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    def _style_header_row(self, ws, row: int, cols: int):
        for col in range(1, cols + 1):
            cell = ws.cell(row=row, column=col)
            cell.fill = self._HEADER_FILL
            cell.font = self._HEADER_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = self._BORDER

    def _style_data_row(self, ws, row: int, cols: int, alt: bool = False):
        for col in range(1, cols + 1):
            cell = ws.cell(row=row, column=col)
            if alt:
                cell.fill = self._ALT_FILL
            cell.border = self._BORDER
            cell.alignment = Alignment(horizontal="center", vertical="center")

    def _write_title(self, ws, title: str, subtitle: str, cols: int):
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=cols)
        ws["A1"] = title
        ws["A1"].font = Font(bold=True, size=14, color="003366")
        ws["A1"].alignment = Alignment(horizontal="center")

        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=cols)
        ws["A2"] = subtitle
        ws["A2"].font = Font(size=10, color="666666", italic=True)
        ws["A2"].alignment = Alignment(horizontal="center")

    def _write_machine_sheet(self, ws_or_wb, items, period_vi: str, date_range: str):
        ws = ws_or_wb.create_sheet(title="Sản lượng theo máy")

        headers = ["Kỳ", "Máy", "Line", "Sản lượng (kg)", "Phế Run (kg)", "Phế Setup (kg)", "Tổng Phế (kg)"]
        self._write_title(ws, f"SẢN LƯỢNG THEO MÁY – Theo {period_vi}", date_range, len(headers))

        for col, h in enumerate(headers, 1):
            ws.cell(row=3, column=col, value=h)
        self._style_header_row(ws, 3, len(headers))

        for i, item in enumerate(items, 4):
            ws.cell(row=i, column=1, value=item.period_label)
            ws.cell(row=i, column=2, value=item.machine_name)
            ws.cell(row=i, column=3, value=item.line)
            ws.cell(row=i, column=4, value=item.total_weight)
            ws.cell(row=i, column=5, value=item.run_waste)
            ws.cell(row=i, column=6, value=item.setup_waste)
            ws.cell(row=i, column=7, value=item.total_waste)
            self._style_data_row(ws, i, len(headers), alt=(i % 2 == 0))

        # Tổng cộng
        total_row = len(items) + 4
        ws.cell(row=total_row, column=1, value="TỔNG").font = Font(bold=True)
        ws.cell(row=total_row, column=4, value=sum(x.total_weight for x in items)).number_format = "#,##0.00"
        ws.cell(row=total_row, column=5, value=sum(x.run_waste for x in items)).number_format = "#,##0.00"
        ws.cell(row=total_row, column=6, value=sum(x.setup_waste for x in items)).number_format = "#,##0.00"
        ws.cell(row=total_row, column=7, value=sum(x.total_waste for x in items)).number_format = "#,##0.00"
        self._style_data_row(ws, total_row, len(headers))
        for col in range(1, len(headers) + 1):
            ws.cell(row=total_row, column=col).font = Font(bold=True)

        # Cột rộng
        col_widths = [14, 18, 8, 16, 16, 16, 16]
        for col, w in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = w

    def _write_waste_sheet(self, ws_or_wb, items, period_vi: str, date_range: str):
        ws = ws_or_wb.create_sheet(title="Phế theo máy")
        headers = ["Kỳ", "Máy", "Line", "Phế Run (kg)", "Phế Setup (kg)", "Tổng Phế (kg)", "Phế Run / Sản lượng %"]
        self._write_title(ws, f"PHẾ THEO MÁY – Theo {period_vi}", date_range, len(headers))

        for col, h in enumerate(headers, 1):
            ws.cell(row=3, column=col, value=h)
        self._style_header_row(ws, 3, len(headers))

        for i, item in enumerate(items, 4):
            pct = round(item.run_waste / item.total_weight * 100, 2) if item.total_weight > 0 else 0
            ws.cell(row=i, column=1, value=item.period_label)
            ws.cell(row=i, column=2, value=item.machine_name)
            ws.cell(row=i, column=3, value=item.line)
            ws.cell(row=i, column=4, value=item.run_waste)
            ws.cell(row=i, column=5, value=item.setup_waste)
            ws.cell(row=i, column=6, value=item.total_waste)
            ws.cell(row=i, column=7, value=pct)
            self._style_data_row(ws, i, len(headers), alt=(i % 2 == 0))

        col_widths = [14, 18, 8, 16, 16, 16, 22]
        for col, w in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = w

    def _write_product_sheet(self, ws_or_wb, items, period_vi: str, date_range: str):
        ws = ws_or_wb.create_sheet(title="Sản lượng theo mã SP")
        headers = ["Kỳ", "Mã sản phẩm", "Sản lượng (kg)"]
        self._write_title(ws, f"SẢN LƯỢNG THEO MÃ SẢN PHẨM – Theo {period_vi}", date_range, len(headers))

        for col, h in enumerate(headers, 1):
            ws.cell(row=3, column=col, value=h)
        self._style_header_row(ws, 3, len(headers))

        for i, item in enumerate(items, 4):
            ws.cell(row=i, column=1, value=item.period_label)
            ws.cell(row=i, column=2, value=item.item_code)
            ws.cell(row=i, column=3, value=item.total_weight)
            self._style_data_row(ws, i, len(headers), alt=(i % 2 == 0))

        # Tổng
        total_row = len(items) + 4
        ws.cell(row=total_row, column=1, value="TỔNG").font = Font(bold=True)
        ws.cell(row=total_row, column=3, value=sum(x.total_weight for x in items))
        self._style_data_row(ws, total_row, len(headers))
        for col in range(1, len(headers) + 1):
            ws.cell(row=total_row, column=col).font = Font(bold=True)

        col_widths = [14, 22, 18]
        for col, w in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = w