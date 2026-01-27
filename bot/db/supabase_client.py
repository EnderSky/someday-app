from supabase import create_client, Client
from config.settings import settings

# Initialize Supabase client with service_role key
# This bypasses RLS for bot operations
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def get_client() -> Client:
    """Get the Supabase client instance."""
    return supabase
