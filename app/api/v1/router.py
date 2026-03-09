from fastapi import APIRouter
from app.api.v1.endpoints import (
    departments,
    employees,
    machine_statuses,
    material_batches,
    material_inventorys,
    po_headers, 
    suppliers,
    materials,
    machines,
    products,
    shifts,
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
    import_declarations,
    warehouses,
    material_receipts,
    iqc_results,
    material_exports,
    weaving_productions,
    logs,
    product_types,
    machine_types,
    areas,
    machine_statuses,
    machine_assignments,
    employee_groups,
    supplier_categories,
    material_types,
    incoterms,
    po_statuses,
    po_details

)

api_router = APIRouter()

api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
api_router.include_router(employees.router, prefix="/employees", tags=["Employees"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["Suppliers"])
api_router.include_router(materials.router, prefix="/materials", tags=["Materials"])
api_router.include_router(machines.router, prefix="/machines", tags=["Machines"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(shifts.router, prefix="/shifts", tags=["Shifts"])
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
api_router.include_router(import_declarations.router, prefix="/import-declarations", tags=["Import Declarations"])
api_router.include_router(warehouses.router, prefix="/warehouses", tags=["Warehouses"])
api_router.include_router(material_receipts.router, prefix="/material-receipts", tags=["Material Receipts"])
api_router.include_router(material_batches.router, prefix="/batches", tags=["Batches"])
api_router.include_router(iqc_results.router, prefix="/iqc-results", tags=["Iqc Results"])
api_router.include_router(material_inventorys.router, prefix="/inventories", tags=["Inventories"])
api_router.include_router(material_exports.router, prefix="/material-exports", tags=["Material Exports"])
api_router.include_router(weaving_productions.router, prefix="/weaving-productions", tags=["Weaving Productions"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(product_types.router, prefix="/product-types", tags=["Product Types"])
api_router.include_router(machine_types.router, prefix="/machine-types", tags=["Machine Types"])
api_router.include_router(machine_statuses.router, prefix="/machine-statuses", tags=["Machine Statuses"])
api_router.include_router(areas.router, prefix="/areas", tags=["Areas"])
api_router.include_router(machine_assignments.router, prefix="/machine-assignments", tags=["Machine Assignments"])
api_router.include_router(employee_groups.router, prefix="/employee-groups", tags=["Employee Groups"])
api_router.include_router(supplier_categories.router, prefix="/supplier-categories", tags=["Supplier Categories"])
api_router.include_router(material_types.router, prefix="/material-types", tags=["Material Types"])
api_router.include_router(incoterms.router, prefix="/incoterms", tags=["Incoterm"])
api_router.include_router(po_statuses.router, prefix="/po-statuses", tags=["PO Status"])
api_router.include_router(po_headers.router, prefix="/purchase-orders", tags=["Purchase Order"])
api_router.include_router(po_details.router, prefix="/po-details", tags=["Purchase Order Detail"])