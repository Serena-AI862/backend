from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Union
from app.core.database import supabase, CALLS_TABLE
from app.schemas.schema import DashboardData
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_duration(seconds: int) -> str:
    """Convert seconds to MM:SS format"""
    if not seconds:
        return "0:00"
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{str(seconds).zfill(2)}"

def calculate_percentage_change(previous: float, current: float) -> float:
    """Calculate percentage change between two values"""
    if previous == 0:
        return 0
    return round(((current - previous) / previous) * 100, 1)

def calculate_avg_rating(call_data: List[Dict]) -> float:
    """Calculate average rating from call data"""
    if not call_data:
        return 0
    ratings = [call.get('rating', 0) for call in call_data if call.get('rating') is not None]
    return sum(ratings) / len(ratings) if ratings else 0

async def get_calls_in_date_range(start_date: datetime, end_date: datetime) -> List[Dict]:
    """Get calls within a specific date range"""
    response = supabase.table(CALLS_TABLE) \
        .select('*') \
        .gte('created_at', start_date.isoformat()) \
        .lt('created_at', end_date.isoformat()) \
        .execute()
    return response.data

async def get_recent_calls(limit: int = 0) -> List[Dict]:
    """Fetch most recent calls with specific fields and formatted duration."""
    query = supabase.table(CALLS_TABLE) \
        .select('from_number, call_type, appointment_booked, rating, created_at, duration') \
        .order('created_at', desc=True)
    
    if limit > 0:
        query = query.limit(limit)
    
    response = query.execute()
    
    return [{
        'number': call['from_number'],
        'call_type': call['call_type'],
        'appointment': 'Yes' if call['appointment_booked'] else 'No',
        'rating': call['rating'] or 0,
        'call_time': datetime.fromisoformat(call['created_at']).strftime('%H:%M'),
        'duration': format_duration(call['duration'])
    } for call in response.data]

async def get_current_week_calls(from_date: Union[str, date]) -> List[Dict]:
    """Fetch all calls from a specific date up to now."""
    try:
        if isinstance(from_date, date):
            iso_date = from_date.isoformat()
        else:
            dt = datetime.strptime(from_date, "%Y-%m-%d")
            iso_date = dt.isoformat()
    except ValueError:
        raise ValueError("Invalid date format. Expected YYYY-MM-DD or datetime.date object.")

    response = supabase.table(CALLS_TABLE) \
        .select('*') \
        .gte('created_at', iso_date) \
        .order('created_at', desc=True) \
        .execute()
    return response.data

async def get_daily_stats(start_date: datetime) -> List[Dict]:
    """Get daily call statistics for the last 7 days"""
    response = supabase.table(CALLS_TABLE) \
        .select('created_at, rating') \
        .gte('created_at', start_date.isoformat()) \
        .order('created_at') \
        .execute()
    
    # Process the data in Python
    daily_stats = {}
    for call in response.data:
        date = datetime.fromisoformat(call['created_at']).date()
        if date not in daily_stats:
            daily_stats[date] = {'total_calls': 0, 'total_rating': 0}
        daily_stats[date]['total_calls'] += 1
        if call['rating'] is not None:
            daily_stats[date]['total_rating'] += call['rating']
    
    # Convert to list format
    return [{
        'date': date.isoformat(),
        'total_calls': stats['total_calls'],
        'avg_rating': round(stats['total_rating'] / stats['total_calls'], 2) if stats['total_calls'] > 0 else 0
    } for date, stats in daily_stats.items()]

async def get_agent_stats(start_date: datetime) -> List[Dict]:
    """Get statistics per agent for the last 30 days"""
    # First get all calls in the date range
    response = supabase.table(CALLS_TABLE) \
        .select('agent_id, rating, appointment_booked') \
        .gte('created_at', start_date.isoformat()) \
        .execute()
    
    # Process the data in Python
    agent_stats = {}
    for call in response.data:
        agent_id = call['agent_id']
        if agent_id not in agent_stats:
            agent_stats[agent_id] = {
                'total_calls': 0,
                'total_rating': 0,
                'appointments_booked': 0
            }
        agent_stats[agent_id]['total_calls'] += 1
        if call['rating'] is not None:
            agent_stats[agent_id]['total_rating'] += call['rating']
        if call['appointment_booked']:
            agent_stats[agent_id]['appointments_booked'] += 1
    
    # Convert to list format and sort by total calls
    return sorted([
        {
            'agent_id': agent_id,
            'total_calls': stats['total_calls'],
            'avg_rating': round(stats['total_rating'] / stats['total_calls'], 2) if stats['total_calls'] > 0 else 0,
            'appointments_booked': stats['appointments_booked']
        }
        for agent_id, stats in agent_stats.items()
    ], key=lambda x: x['total_calls'], reverse=True)

async def get_call_type_stats(start_date: datetime) -> Dict[str, int]:
    """Get statistics by call type for the last 30 days"""
    # First get all calls in the date range
    response = supabase.table(CALLS_TABLE) \
        .select('call_type') \
        .gte('created_at', start_date.isoformat()) \
        .execute()
    
    # Process the data in Python
    call_type_stats = {}
    for call in response.data:
        call_type = call['call_type']
        call_type_stats[call_type] = call_type_stats.get(call_type, 0) + 1
    
    return call_type_stats

async def get_call_by_id(call_id: str) -> Optional[Dict]:
    """Fetch a specific call by ID"""
    response = supabase.table(CALLS_TABLE) \
        .select('*') \
        .eq('id', call_id) \
        .single() \
        .execute()
    return response.data if response.data else None

async def search_calls(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    agent_id: Optional[str] = None,
    call_type: Optional[str] = None,
    successful: Optional[bool] = None,
    limit: int = 100
) -> List[Dict]:
    """Search calls with various filters"""
    query = supabase.table(CALLS_TABLE).select('*')
    
    if start_date:
        query = query.gte('created_at', start_date.isoformat())
    if end_date:
        query = query.lte('created_at', end_date.isoformat())
    if agent_id:
        query = query.eq('agent_id', agent_id)
    if call_type:
        query = query.eq('call_type', call_type)
    if successful is not None:
        query = query.eq('successful', successful)
    
    response = query.order('created_at', desc=True).limit(limit).execute()
    return response.data 

def calculate_avg_cal_duration(call_data: List[Dict]) -> str:
    """Calculate average call duration from a list of calls.
    
    Args:
        call_data: List of call dictionaries containing duration_seconds
        
    Returns:
        str: Average duration in format "MM:SS"
    """
    if not call_data:
        return "0:00"
        
    # Get all valid durations (filter out None values)
    durations = [call.get('duration', 0) for call in call_data if call.get('duration') is not None]
        
    # Calculate average in seconds
    avg_seconds = int(sum(durations) / len(durations))
    
    # Convert to minutes and seconds
    minutes = avg_seconds // 60
    seconds = avg_seconds % 60
    
    # Format as MM:SS with leading zeros for seconds
    return f"{minutes}:{str(seconds).zfill(2)}" 

def calculate_percentage_duration_change(previous: str, current: str) -> float:
    """Calculate percentage change between two duration strings in MM:SS format."""
    def duration_to_seconds(duration: str) -> int:
        """Convert MM:SS format to total seconds"""
        try:
            minutes, seconds = map(int, duration.split(':'))
            return minutes * 60 + seconds
        except (ValueError, AttributeError):
            return 0
            
    prev_seconds = duration_to_seconds(previous)
    curr_seconds = duration_to_seconds(current)
    
    if prev_seconds == 0:
        return 0
        
    return round(((curr_seconds - prev_seconds) / prev_seconds) * 100, 1)

async def get_dashboard_data() -> DashboardData:
    """Fetch and calculate dashboard statistics from calls data."""
    try:
        # Test database connection
        test_query = supabase.table(CALLS_TABLE).select('*').limit(1).execute()
        logger.info(f"Database connection test result: {test_query}")
        
        # Get current date and calculate date ranges
        now = datetime.now()
        today = now.date()
        last_7_days = today - timedelta(days=7)
        last_14_days = today - timedelta(days=14)
        
        # Fetch calls data for different time periods
        recent_calls = await get_recent_calls()
        current_week_calls = await get_current_week_calls(last_7_days)
        previous_period_calls = await get_calls_in_date_range(last_14_days, last_7_days)
        daily_stats = await get_daily_stats(last_7_days)
        # agent_stats = await get_agent_stats(last_30_days)
        # call_type_stats = await get_call_type_stats(last_30_days)

        # Total calls card
        total_calls = len(current_week_calls)
        # successful_calls = sum(1 for call in current_week_calls if call.get('successful', False))
        prev_total_calls = len(previous_period_calls)
        total_calls_change = calculate_percentage_change(prev_total_calls, total_calls)

        # Appointment booked card
        appointments_booked = sum(1 for call in current_week_calls if call.get('appointment_booked', False))
        prev_appointments_booked = sum(1 for call in previous_period_calls if call.get('appointment_booked', False))
        appointments_change = calculate_percentage_change(prev_appointments_booked, appointments_booked)

        # Avg. call duration card
        avg_call_duration = calculate_avg_cal_duration(current_week_calls)
        prev_avg_call_duration = calculate_avg_cal_duration(previous_period_calls)
        avg_call_duration_change = calculate_percentage_duration_change(prev_avg_call_duration, avg_call_duration)

        # Avg. rating card
        avg_rating = calculate_avg_rating(current_week_calls)
        prev_avg_rating = calculate_avg_rating(previous_period_calls)
        avg_rating_change = calculate_percentage_change(prev_avg_rating, avg_rating)

        # Calculate percentage changes
        # successful_calls_change = calculate_percentage_change(prev_successful_calls, successful_calls)
        
        logger.info(f"Recent calls: {len(recent_calls)}")   
        logger.info(f"Current week calls: {len(current_week_calls)}")
        logger.info(f"Previous period calls: {len(previous_period_calls)}")
        return DashboardData(
            total_calls=total_calls,
            total_calls_change=total_calls_change,
            appointments_booked=appointments_booked,
            appointments_change=appointments_change,
            avg_call_duration=avg_call_duration,
            avg_call_duration_change=avg_call_duration_change,
            avg_rating=round(avg_rating, 2),
            avg_rating_change=avg_rating_change,
            daily_stats=daily_stats,
            recent_calls=recent_calls,
            # successful_calls=successful_calls,
            # successful_calls_change=successful_calls_change,
            # agent_stats=agent_stats,
            # call_type_stats=call_type_stats
        )
    except Exception as e:
        logger.error(f"Error in get_dashboard_data: {str(e)}")
        raise