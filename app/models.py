from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

# Base models for database
class CallBase(BaseModel):
    user_id: int
    timestamp: datetime
    duration_seconds: Optional[int] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    appointment_booked: bool = False
    notes: Optional[str] = None
    call_type: str = "inquiry"  # inquiry, complaint, etc.

class CallCreate(CallBase):
    pass

class Call(CallBase):
    id: int
    
    class Config:
        from_attributes = True

# Dashboard specific models
class DashboardCallStats(BaseModel):
    total_calls: int
    total_calls_change: float
    appointments_booked: int
    appointments_change: float
    avg_duration: str
    duration_change: float
    avg_rating: float
    rating_change: float
    call_to_appointment_rate: Optional[float] = None
    missed_calls_percentage: Optional[float] = None
    top_performing_day: Optional[str] = None
    peak_call_hours: Optional[str] = None

class DashboardCallVolume(BaseModel):
    day: str
    calls: int

class DashboardCall(BaseModel):
    phone_number: str
    duration: str
    call_type: str
    appointment: str
    rating: int
    call_time: str

class DashboardData(BaseModel):
    call_stats: DashboardCallStats
    call_volume: List[DashboardCallVolume]
    recent_calls: List[DashboardCall] 