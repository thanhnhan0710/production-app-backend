from fastapi import APIRouter
from app.api.v1.endpoints import (
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
    material_issue_slips,
    material_issue_slip_details,
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
api_router.include_router(material_issue_slips.router, prefix="/material-issue-slips", tags=["Material Issue Slips"])
api_router.include_router(material_issue_slip_details.router, prefix="/material-issue-slip-details", tags=["Material Issue Slip Details"])
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


