import streamlit as st
import pandas as pd
from lib.supabase_client import get_company_stats, get_receipts, get_current_user

if not st.session_state.get("logged_in"):
    st.warning("請先登入 Please login first")
    st.stop()

user = get_current_user()
company_id = st.session_state.company_id

st.title("📊 Dashboard")

stats = get_company_stats(company_id)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("收據總數 Total Receipts", stats.get("total_receipts", 0))
with col2:
    st.metric("總金額 Total Amount", f"HK${stats.get('total_amount', 0):,.2f}")
with col3:
    st.metric("待審批 Pending Approvals", stats.get("pending_approvals", 0))
with col4:
    st.metric("本月支出 This Month", f"HK${stats.get('this_month_amount', 0):,.2f}")

st.divider()

st.subheader("月度支出 Monthly Spending by Category")
category_data = stats.get("monthly_by_category", [])
if category_data:
    df_chart = pd.DataFrame(category_data)
    st.bar_chart(df_chart, x="month", y="amount", color="category")
else:
    st.info("暫無數據 No data available")

st.divider()

st.subheader("最近收據 Recent Receipts")
recent = get_receipts(company_id, {"limit": 5, "order_by": "created_at", "ascending": False})
if recent:
    for r in recent:
        with st.expander(f"{r.get('merchant_name', 'Unknown')} — HK${r.get('total_amount', 0):,.2f}"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**日期 Date:** {r.get('receipt_date', 'N/A')}")
                st.write(f"**類型 Type:** {r.get('receipt_type', 'N/A')}")
                st.write(f"**狀態 Status:** {r.get('status', 'N/A')}")
            with col_b:
                st.write(f"**備註 Notes:** {r.get('notes', '')}")
else:
    st.info("暫無收據 No receipts yet")

if st.session_state.role in ("admin", "manager"):
    st.divider()
    st.subheader("🏢 公司概覽 Company Summary")
    company_stats = stats.get("company_summary", {})
    if company_stats:
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            st.metric("員工數 Employees", company_stats.get("employee_count", 0))
        with col_e2:
            st.metric("本月提交 Submissions This Month", company_stats.get("submissions_this_month", 0))
        with col_e3:
            st.metric("待審批 Pending", company_stats.get("pending_count", 0))
