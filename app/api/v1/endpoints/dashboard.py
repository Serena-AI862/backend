from fastapi import APIRouter, Depends
from app.services.calls import get_dashboard_data
from app.schemas.schema import DashboardData

router = APIRouter()

@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard():
    """
    Get dashboard statistics and data.
    Returns aggregated data for the dashboard display including:
    - Total calls
    - Appointments booked
    - Average call duration
    - Average rating
    - Daily statistics
    - Call type distribution
    - Recent calls
    - Successful calls
    - Agent statistics
    """
    return await get_dashboard_data() 