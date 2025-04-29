from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel

class DashboardData(BaseModel):
    total_calls: int
    total_calls_change: float
    appointments_booked: int
    appointments_change: float
    avg_call_duration: str
    avg_call_duration_change: float
    avg_rating: float
    avg_rating_change: float
    daily_stats: List[Dict]
    recent_calls: List[Dict]
    # call_type_stats: Dict[str, int] 
    # successful_calls: int
    # successful_calls_change: float
    # agent_stats: List[Dict]