from fastapi import APIRouter
from app.api.v1.endpoints import (
    batches,
    departments,
    employees, 
    yarns,
    suppliers,
    yarn_lots,
    materials,
    machines,
    products,
    shifts,
    yarn_issue_slips,
    yarn_issue_slip_details,
    units,
    baskets,
    dye_colors,
    standards,
    work_schedules,
    weaving_basket_tickets,
    weaving_inspections,
    inventory_semis,
    login,
    users,
    upload,
    weaving_daily_productions,
    boms,
    purchase_orders,
    import_declarations,
    warehouses,
    material_receipts,
    iqc_results,
    inventorys,
    material_exports
)

api_router = APIRouter()

api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
api_router.include_router(employees.router, prefix="/employees", tags=["Employees"])
api_router.include_router(yarns.router, prefix="/yarns", tags=["Yarns"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["Suppliers"])
api_router.include_router(yarn_lots.router, prefix="/yarn-lots", tags=["Yarn Lots"])
api_router.include_router(materials.router, prefix="/materials", tags=["Materials"])
api_router.include_router(machines.router, prefix="/machines", tags=["Machines"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(shifts.router, prefix="/shifts", tags=["Shifts"])
api_router.include_router(yarn_issue_slips.router, prefix="/yarn-issue-slips", tags=["Yarn Issue Slips"])
api_router.include_router(yarn_issue_slip_details.router, prefix="/yarn-issue-slip-details", tags=["Yarn Issue Slip Details"])
api_router.include_router(units.router, prefix="/units", tags=["Units"])
api_router.include_router(baskets.router, prefix="/baskets", tags=["Baskets"])
api_router.include_router(dye_colors.router, prefix="/dye-colors", tags=["Dye Colors"])
api_router.include_router(standards.router, prefix="/standards", tags=["Standards"])
api_router.include_router(work_schedules.router, prefix="/work-schedules", tags=["Work Schedules"])
api_router.include_router(weaving_basket_tickets.router, prefix="/weaving-basket-tickets", tags=["Weaving Basket Tickets"])
api_router.include_router(weaving_inspections.router, prefix="/weaving-inspections", tags=["Weaving Inspections"])
api_router.include_router(inventory_semis.router, prefix="/inventory-semis", tags=["Inventory Semis"])
api_router.include_router(login.router, tags=["login"], prefix="/login")
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
api_router.include_router(weaving_daily_productions.router, prefix="/weaving-daily-productions", tags=["Weaving Daily Productions"])
# Ví dụ trong app/api/v1/api.py
api_router.include_router(boms.router, prefix="/boms", tags=["BOM"])
api_router.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["Purchase Orders"])
api_router.include_router(import_declarations.router, prefix="/import-declarations", tags=["Import Declarations"])
api_router.include_router(warehouses.router, prefix="/warehouses", tags=["Warehouses"])
api_router.include_router(material_receipts.router, prefix="/material-receipts", tags=["Material Receipts"])
api_router.include_router(batches.router, prefix="/batches", tags=["Batches"])
api_router.include_router(iqc_results.router, prefix="/iqc-results", tags=["Iqc Results"])
api_router.include_router(inventorys.router, prefix="/inventorys", tags=["Inventorys"])
api_router.include_router(material_exports.router, prefix="/material-exports", tags=["Material Exports"])

