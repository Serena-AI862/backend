from supabase import create_client, Client
from app.core.config import settings

supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
)

# Database Tables
USERS_TABLE = "users"
CALLS_TABLE = "calls" 