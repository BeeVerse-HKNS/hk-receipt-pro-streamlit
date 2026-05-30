import streamlit as st
import pandas as pd
from lib.supabase_client import (
    get_receipts,
    update_receipt,
    delete_receipt,
    get_receipt_image_url,
    get_current_user,
)

RECEIPT_TYPES = {
    "office_supplies": "辦公用品 Office Supplies",
    "meals_entertainment": "膳食及應酬 Meals & Entertainment",
    "transportation": "交通費 Transportation",
    "utilities": "水電費 Utilities",
    "rent_rates": "租金及差餉 Rent & Rates",
    "professional_fees": "專業費用 Professional Fees",
    "insurance": "保險 Insurance",
    "repairs_maintenance": "維修保養 Repairs & Maintenance",
    "travel": "差旅費 Travel",
    "marketing": "市場推廣 Marketing",
    "depreciation": "折舊 Depreciation",
    "miscellaneous": "雜項 Miscellaneous",
}

TYPE_KEYS = list(RECEIPT_TYPES.keys())

if not st.session_state.get("logged_in"):
    st.warning("請先登入 Please login first")
    st.stop()

user = get_current_user()
company_id = st.session_state.company_id

st.title("🧾 Receipts")

with st.expander("🔍 篩選 Filters", expanded=False):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        date_from = st.date_input("由 From", value=None, key="filter_date_from")
        date_to = st.date_input("至 To", value=None, key="filter_date_to")
    with col2:
        merchant_search = st.text_input("商戶搜尋 Merchant Search", key="filter_merchant")
    with col3:
        type_filter = st.selectbox(
            "類型 Type",
            ["all"] + TYPE_KEYS,
            key="filter_type",
            format_func=lambda x: "全部 All" if x == "all" else RECEIPT_TYPES[x],
        )
    with col4:
        status_filter = st.selectbox(
            "狀態 Status",
            ["all", "draft", "submitted", "approved", "rejected"],
            key="filter_status",
        )

filters = {}
if date_from:
    filters["date_from"] = str(date_from)
if date_to:
    filters["date_to"] = str(date_to)
if merchant_search:
    filters["merchant_search"] = merchant_search
if type_filter != "all":
    filters["receipt_type"] = type_filter
if status_filter != "all":
    filters["status"] = status_filter

receipts = get_receipts(company_id, filters if filters else None)

if receipts:
    df = pd.DataFrame(receipts)
    display_cols = ["merchant_name", "receipt_date", "total_amount", "receipt_type", "status"]
    available_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(
        df[available_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "merchant_name": st.column_config.TextColumn("Merchant"),
            "receipt_date": st.column_config.DateColumn("Date"),
            "total_amount": st.column_config.NumberColumn("Total (HKD)", format="%.2f"),
            "receipt_type": st.column_config.TextColumn("Type"),
            "status": st.column_config.TextColumn("Status"),
        },
    )

    st.divider()
    st.subheader("收據詳情 Receipt Details")

    for r in receipts:
        receipt_label = f"{r.get('merchant_name', 'Unknown')} — HK${r.get('total_amount', 0):,.2f} ({r.get('status', '')})"
        with st.expander(receipt_label):
            col_edit, col_actions = st.columns([3, 1])

            with col_edit:
                edit_key = f"edit_{r.get('id', '')}"
                with st.form(edit_key):
                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                        e_merchant = st.text_input("Merchant", value=r.get("merchant_name", ""), key=f"{edit_key}_merchant")
                        e_date = st.date_input("Date", value=r.get("receipt_date"), key=f"{edit_key}_date")
                        r_type = r.get("receipt_type", "miscellaneous")
                        e_type_index = TYPE_KEYS.index(r_type) if r_type in TYPE_KEYS else TYPE_KEYS.index("miscellaneous")
                        e_type = st.selectbox(
                            "Type",
                            TYPE_KEYS,
                            index=e_type_index,
                            key=f"{edit_key}_type",
                            format_func=lambda x: RECEIPT_TYPES[x],
                        )
                    with e_col2:
                        e_total = st.number_input("Total (HKD)", value=float(r.get("total_amount", 0)), min_value=0.0, step=0.1, key=f"{edit_key}_total")
                        e_notes = st.text_area("Notes", value=r.get("notes", ""), key=f"{edit_key}_notes")

                    save_col, submit_col = st.columns(2)
                    with save_col:
                        save_btn = st.form_submit_button("💾 Update", use_container_width=True)
                    with submit_col:
                        submit_btn = st.form_submit_button("📤 Submit for Approval", use_container_width=True)

                    if save_btn:
                        update_data = {
                            "merchant_name": e_merchant,
                            "receipt_date": str(e_date),
                            "total_amount": e_total,
                            "tax_amount": 0.0,
                            "receipt_type": e_type,
                            "notes": e_notes,
                        }
                        result = update_receipt(r["id"], update_data)
                        if result:
                            st.success("✅ 已更新 Updated!")
                            st.rerun()
                        else:
                            st.error("更新失敗 Update failed")

                    if submit_btn:
                        update_data = {
                            "merchant_name": e_merchant,
                            "receipt_date": str(e_date),
                            "total_amount": e_total,
                            "tax_amount": 0.0,
                            "receipt_type": e_type,
                            "notes": e_notes,
                            "status": "submitted",
                        }
                        result = update_receipt(r["id"], update_data)
                        if result:
                            st.success("✅ 已提交 Submitted for approval!")
                            st.rerun()
                        else:
                            st.error("提交失敗 Submit failed")

            with col_actions:
                if r.get("image_url"):
                    if st.button("🖼️ View Image", key=f"img_{r.get('id', '')}"):
                        url = get_receipt_image_url(r["image_url"])
                        if url:
                            st.image(url)

                if st.button("🗑️ Delete", key=f"del_{r.get('id', '')}", type="secondary"):
                    if delete_receipt(r["id"]):
                        st.success("已刪除 Deleted!")
                        st.rerun()
                    else:
                        st.error("刪除失敗 Delete failed")
else:
    st.info("暫無收據 No receipts found. Upload your first receipt!")
