import sys
from supabase import create_client

SUPABASE_URL = "https://kqdrupnrdtsjsfcorlwg.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtxZHJ1cG5yZHRzanNmY29ybHdnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MDEyNDQ0MCwiZXhwIjoyMDk1NzAwNDQwfQ.SFKtLit1EzSPUO3G5X_chLBM1jgPtY8h6eQqdBmSxzk"

ADMIN_EMAIL = "admin@beeverse.io"
ADMIN_PASSWORD = "BeeVerse2026!HKRP"
COMPANY_NAME = "BeeVerse HK Receipt Pro"


def main():
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    print(f"Creating admin user: {ADMIN_EMAIL}")
    try:
        auth_resp = client.auth.admin.create_user({
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "email_confirm": True,
        })
        user = auth_resp.user
        user_id = user.id
        print(f"  User created: {user_id}")
    except Exception as e:
        err_msg = str(e)
        if "already been registered" in err_msg or "already exists" in err_msg:
            print(f"  User already exists, looking up user ID...")
            users_resp = client.auth.admin.list_users()
            for u in users_resp:
                if u.email == ADMIN_EMAIL:
                    user_id = u.id
                    print(f"  Found existing user: {user_id}")
                    break
            else:
                print(f"  ERROR: Could not find existing user by email")
                sys.exit(1)
        else:
            print(f"  ERROR creating user: {e}")
            sys.exit(1)

    print(f"Creating company: {COMPANY_NAME}")
    try:
        company_resp = client.table("companies").insert({
            "name": COMPANY_NAME,
        }).execute()
        company_id = company_resp.data[0]["id"]
        print(f"  Company created: {company_id}")
    except Exception as e:
        err_msg = str(e)
        if "duplicate key" in err_msg or "already exists" in err_msg.lower():
            print(f"  Company already exists, looking up company ID...")
            comp_resp = client.table("companies").select("id").eq("name", COMPANY_NAME).single().execute()
            company_id = comp_resp.data["id"]
            print(f"  Found existing company: {company_id}")
        else:
            print(f"  ERROR creating company: {e}")
            sys.exit(1)

    print("Creating admin profile")
    try:
        profile_resp = client.table("profiles").insert({
            "id": user_id,
            "name": "BeeVerse Admin",
            "role": "admin",
            "company_id": company_id,
        }).execute()
        profile_id = profile_resp.data[0]["id"]
        print(f"  Profile created: {profile_id}")
    except Exception as e:
        err_msg = str(e)
        if "duplicate key" in err_msg or "already exists" in err_msg.lower():
            print(f"  Profile already exists, looking up profile ID...")
            prof_resp = client.table("profiles").select("id").eq("id", user_id).single().execute()
            profile_id = prof_resp.data["id"]
            print(f"  Found existing profile: {profile_id}")
        else:
            print(f"  ERROR creating profile: {e}")
            sys.exit(1)

    print()
    print("=" * 50)
    print("Production admin account created successfully!")
    print("=" * 50)
    print(f"  User ID:    {user_id}")
    print(f"  Company ID: {company_id}")
    print(f"  Profile ID: {profile_id}")
    print(f"  Email:      {ADMIN_EMAIL}")
    print(f"  Role:       admin")


if __name__ == "__main__":
    main()
