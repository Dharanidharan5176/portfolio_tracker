from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    system,
    portfolios,
    accounts,
    transactions,
    holdings,
    dashboard,
    performance,
    allocation,
    income,
    imports,
    data_quality,
    notifications,
    reports,
    settings_endpoint,
    jobs,
    backups
)

api_router = APIRouter()

api_router.include_router(system.router, prefix="/system", tags=["System"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["Portfolios"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(holdings.router, prefix="/holdings", tags=["Holdings"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(performance.router, prefix="/performance", tags=["Performance"])
api_router.include_router(allocation.router, prefix="/allocation", tags=["Allocation"])
api_router.include_router(income.router, prefix="/income", tags=["Income"])
api_router.include_router(imports.router, prefix="/imports", tags=["Imports"])
api_router.include_router(data_quality.router, prefix="/data-quality", tags=["Data Quality"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(settings_endpoint.router, prefix="/settings", tags=["Settings"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(backups.router, prefix="/backups", tags=["Backups"])
