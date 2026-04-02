# backend/services/supabase_client.py

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()  # reads your .env file

# Create a single shared client (not one per request — that's wasteful)
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")  # service key bypasses RLS for backend ops
)

def get_supabase() -> Client:
    return supabase