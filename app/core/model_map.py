# app/core/model_map.py
from app.models.machine import Machine
from app.models.product import Product
from app.models.user import User
from app.models.department import Department
from app.models.employee import Employee
from app.models.supplier import Supplier
from app.models.basket import Basket
from app.models.shift import Shift
from app.models.unit import Unit
from app.models.machine_type import MachineType
from app.models.material import Material
from app.models.weaving_basket_ticket import WeavingBasketTicket, WeavingTicketYarn
from app.models.weaving_inspection import WeavingInspection
from app.models.standard import Standard
from app.models.dye_color import DyeColor
from app.models.bom_header import BOMHeader
from app.models.bom_detail import BOMDetail
from app.models.import_declaration import ImportDeclaration,ImportDeclarationDetail
from app.models.warehouse import Warehouse
from app.models.material_receipt import MaterialReceipt,MaterialReceiptDetail
from app.models.batch import Batch
from app.models.iqc_result import IQCResult
from app.models.material_export import MaterialExport,MaterialExportDetail
from app.models.machine_log import MachineLog
from app.models.weaving_production import WeavingProduction
from app.models.product_type import ProductType
from app.models.machine_type import MachineType
from app.models.machine_status import MachineStatus
from app.models.area import Area
from app.models.machine_product_history import MachineProductHistory
from app.models.employee_group import EmployeeGroup
from app.models.supplier_category import SupplierCategory
from app.models.incoterm import Incoterm
from app.models.po_status import POStatus
from app.models.po_header import PurchaseOrderHeader
from app.models.po_detail import PurchaseOrderDetail
# Import thêm các model khác của bạn ở đây...

# Dictionary ánh xạ: "tên_bảng" -> ModelClass
MODEL_MAPPING = {
    "machine_types": MachineType,
    "machine_statuses": MachineStatus,
    "areas": Area,
    "machines": Machine,
    "products": Product,
    "users": User,
    "departments":Department,
    "employees":Employee,
    "suppliers":Supplier,
    "baskets":Basket,
    "shift":Shift,
    "units":Unit,
    "material_types":MachineType,
    "materials":Material,
    "weaving_ticket_yarns":WeavingTicketYarn,
    "weaving_basket_tickets":WeavingBasketTicket,
    "weaving_inspections":WeavingInspection,
    "standards":Standard,
    "dye_colors":DyeColor,
    "bom_headers":BOMHeader,
    "bom_details":BOMDetail,
    "purchase_orders":PurchaseOrderHeader,
    "purchase_order_details":PurchaseOrderDetail,
    "import_declarations":ImportDeclaration,
    "import_declaration_details":ImportDeclarationDetail,
    "warehouses":Warehouse,
    "material_receipts":MaterialReceipt,
    "material_receipt_details":MaterialReceiptDetail,
    "batches":Batch,
    "iqc_results":IQCResult,
    "material_exports":MaterialExport,
    "material_export_details":MaterialExportDetail,
    "machine_logs":MachineLog,
    "weaving_productions":WeavingProduction,
    "product_types":ProductType,
    "machine_product_histories": MachineProductHistory,
    "employee_groups":EmployeeGroup,
    "supplier_categories":SupplierCategory,
    "incoterms":Incoterm,
    "po_statuses":POStatus,


    # Thêm các bảng khác vào đây...
}

def get_model_by_tablename(tablename: str):
    return MODEL_MAPPING.get(tablename)