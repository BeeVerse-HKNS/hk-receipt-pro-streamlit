import streamlit as st
from supabase import create_client, Client
import uuid
from datetime import datetime


def get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    if "supabase_client" not in st.session_state:
        st.session_state.supabase_client = create_client(url, key)
    return st.session_state.supabase_client


def get_admin_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


def sign_in(email: str, password: str) -> dict:
    try:
        client = get_client()
        response = client.auth.sign_in_with_password({"email": email, "password": password})
        user = response.user
        profile_resp = client.table("profiles").select("*").eq("id", user.id).single().execute()
        profile = profile_resp.data if profile_resp.data else {}
        return {"user": user, "profile": profile}
    except Exception as e:
        st.error(f"Login error: {e}")
        return None


def sign_up(email: str, password: str, company_name: str) -> dict:
    try:
        admin_client = get_admin_client()
        auth_resp = admin_client.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
        })
        user = auth_resp.user

        company_resp = admin_client.table("companies").insert({
            "name": company_name,
        }).execute()
        company_id = company_resp.data[0]["id"]

        admin_client.table("profiles").insert({
            "id": user.id,
            "name": company_name + " Admin",
            "role": "admin",
            "company_id": company_id,
        }).execute()

        return {"user": user, "company_id": company_id}
    except Exception as e:
        return {"error": str(e)}


def sign_out():
    try:
        client = get_client()
        client.auth.sign_out()
    except Exception:
        pass
    keys_to_clear = ["logged_in", "user_id", "email", "role", "company_id", "supabase_client", "ocr_result", "report_df", "report_receipts"]
    for key in keys_to_clear:
        st.session_state.pop(key, None)


def get_current_user() -> dict:
    if not st.session_state.get("logged_in"):
        return None
    return {
        "id": st.session_state.user_id,
        "email": st.session_state.email,
        "role": st.session_state.role,
        "company_id": st.session_state.company_id,
    }


def create_receipt(data: dict) -> dict:
    try:
        client = get_client()
        resp = client.table("receipts").insert(data).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        st.error(f"Create receipt error: {e}")
        return None


def get_receipts(company_id: str, filters: dict = None) -> list:
    try:
        client = get_client()
        query = client.table("receipts").select("*").eq("company_id", company_id)
        if filters:
            if filters.get("date_from"):
                query = query.gte("receipt_date", filters["date_from"])
            if filters.get("date_to"):
                query = query.lte("receipt_date", filters["date_to"])
            if filters.get("merchant_search"):
                query = query.ilike("merchant_name", f"%{filters['merchant_search']}%")
            if filters.get("receipt_type"):
                query = query.eq("receipt_type", filters["receipt_type"])
            if filters.get("status"):
                query = query.eq("status", filters["status"])
            if filters.get("limit"):
                query = query.limit(filters["limit"])
            if filters.get("order_by"):
                ascending = filters.get("ascending", False)
                query = query.order(filters["order_by"], desc=not ascending)
        else:
            query = query.order("created_at", desc=True)
        resp = query.execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error(f"Get receipts error: {e}")
        return []


def update_receipt(receipt_id: str, data: dict) -> dict:
    try:
        client = get_client()
        resp = client.table("receipts").update(data).eq("id", receipt_id).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        st.error(f"Update receipt error: {e}")
        return None


def delete_receipt(receipt_id: str) -> bool:
    try:
        client = get_client()
        resp = client.table("receipts").delete().eq("id", receipt_id).execute()
        return True
    except Exception as e:
        st.error(f"Delete receipt error: {e}")
        return False


def upload_receipt_image(file_bytes: bytes, filename: str, company_id: str) -> str:
    try:
        client = get_client()
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
        storage_path = f"{company_id}/{uuid.uuid4().hex}.{ext}"
        content_type = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "heic": "image/heic",
        }.get(ext.lower(), "image/jpeg")
        client.storage.from_("receipts").upload(storage_path, file_bytes, {"content-type": content_type})
        return storage_path
    except Exception as e:
        st.error(f"Upload image error: {e}")
        return None


def get_receipt_image_url(storage_path: str) -> str:
    try:
        client = get_client()
        resp = client.storage.from_("receipts").create_signed_url(storage_path, 3600)
        return resp.get("signedURL") or resp if isinstance(resp, str) else None
    except Exception as e:
        st.error(f"Get image URL error: {e}")
        return None


def get_company_stats(company_id: str) -> dict:
    try:
        client = get_client()
        receipts_resp = client.table("receipts").select("total_amount, tax_amount, receipt_type, receipt_date, status, created_at").eq("company_id", company_id).execute()
        receipts = receipts_resp.data if receipts_resp.data else []

        total_receipts = len(receipts)
        total_amount = sum(float(r.get("total_amount", 0)) for r in receipts)
        pending_approvals = len([r for r in receipts if r.get("status") == "submitted"])

        now = datetime.now()
        this_month_receipts = [
            r for r in receipts
            if r.get("receipt_date", "")[:7] == now.strftime("%Y-%m")
        ]
        this_month_amount = sum(float(r.get("total_amount", 0)) for r in this_month_receipts)

        monthly_by_category = []
        category_month = {}
        for r in receipts:
            key = (r.get("receipt_type", "other"), r.get("receipt_date", "")[:7])
            if key not in category_month:
                category_month[key] = 0
            category_month[key] += float(r.get("total_amount", 0))
        for (cat, month), amt in sorted(category_month.items()):
            monthly_by_category.append({"category": cat, "month": month, "amount": amt})

        company_summary = {
            "employee_count": 0,
            "submissions_this_month": len(this_month_receipts),
            "pending_count": pending_approvals,
        }
        try:
            profiles_resp = client.table("profiles").select("id", count="exact").eq("company_id", company_id).execute()
            company_summary["employee_count"] = profiles_resp.count if hasattr(profiles_resp, 'count') else len(profiles_resp.data or [])
        except Exception:
            pass

        return {
            "total_receipts": total_receipts,
            "total_amount": total_amount,
            "pending_approvals": pending_approvals,
            "this_month_amount": this_month_amount,
            "monthly_by_category": monthly_by_category,
            "company_summary": company_summary,
        }
    except Exception as e:
        st.error(f"Get stats error: {e}")
        return {
            "total_receipts": 0,
            "total_amount": 0,
            "pending_approvals": 0,
            "this_month_amount": 0,
            "monthly_by_category": [],
            "company_summary": {},
        }


def list_employees(company_id: str) -> list:
    try:
        client = get_client()
        resp = client.table("profiles").select("id, role, active").eq("company_id", company_id).execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error(f"List employees error: {e}")
        return []


def invite_employee(email: str, role: str, company_id: str) -> dict:
    try:
        admin_client = get_admin_client()
        auth_resp = admin_client.auth.admin.create_user({
            "email": email,
            "password": str(uuid.uuid4()),
            "email_confirm": False,
        })
        user = auth_resp.user
        admin_client.table("profiles").insert({
            "id": user.id,
            "name": email.split("@")[0],
            "role": role,
            "company_id": company_id,
            "active": True,
        }).execute()
        return {"user": user}
    except Exception as e:
        st.error(f"Invite employee error: {e}")
        return None


def approve_receipt(receipt_id: str, approver_id: str) -> dict:
    try:
        client = get_client()
        resp = client.table("receipts").update({
            "status": "approved",
            "approved_by": approver_id,
            "approved_at": datetime.utcnow().isoformat(),
        }).eq("id", receipt_id).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        st.error(f"Approve receipt error: {e}")
        return None


def reject_receipt(receipt_id: str, approver_id: str, reason: str) -> dict:
    try:
        client = get_client()
        resp = client.table("receipts").update({
            "status": "rejected",
            "approved_by": approver_id,
            "approved_at": datetime.utcnow().isoformat(),
            "rejection_reason": reason,
        }).eq("id", receipt_id).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        st.error(f"Reject receipt error: {e}")
        return None


def get_pending_approvals(company_id: str) -> list:
    try:
        client = get_client()
        resp = client.table("receipts").select("*, profiles(email)").eq("company_id", company_id).eq("status", "submitted").execute()
        receipts = resp.data if resp.data else []
        for r in receipts:
            profile = r.pop("profiles", {})
            r["submitted_by_email"] = profile.get("email", "Unknown") if profile else "Unknown"
        return receipts
    except Exception as e:
        st.error(f"Get pending approvals error: {e}")
        return []


def export_user_data(user_id: str) -> dict:
    try:
        admin_client = get_admin_client()
        profile_resp = admin_client.table("profiles").select("*").eq("id", user_id).single().execute()
        receipts_resp = admin_client.table("receipts").select("*").eq("user_id", user_id).execute()
        return {
            "profile": profile_resp.data,
            "receipts": receipts_resp.data if receipts_resp.data else [],
            "exported_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        st.error(f"Export data error: {e}")
        return None


def request_account_deletion(user_id: str) -> bool:
    try:
        admin_client = get_admin_client()
        admin_client.table("profiles").update({
            "deletion_requested": True,
            "deletion_requested_at": datetime.utcnow().isoformat(),
        }).eq("id", user_id).execute()
        return True
    except Exception as e:
        st.error(f"Request deletion error: {e}")
        return False
