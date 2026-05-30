import os
from supabase import create_client

def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        print("ERROR: SUPABASE_URL or SUPABASE_ANON_KEY not set")
        return
    client = create_client(url, key)
    result = client.table("keep_alive_log").insert({"source": "github_actions"}).execute()
    print(f"Keep-alive ping successful: {result.data}")

if __name__ == "__main__":
    main()
