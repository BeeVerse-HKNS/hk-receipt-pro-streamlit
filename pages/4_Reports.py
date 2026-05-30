import streamlit as st
import pandas as pd
from datetime import date
from lib.supabase_client import get_receipts, get_current_user
from lib.excel_export import generate_excel_report, generate_csv_report

if not st.session_state.get("logged_in"):
    st.warning("請先登入 Please login first")
    st.stop()

user = get_current_user()
company_id = st.session_state.company_id

st.title("📈 Reports")

col_period1, col_period2 = st.columns(2)
with col_period1:
    period_from = st.date_input("由 From", value=None, key="report_from")
with col_period2:
    period_to = st.date_input("至 To", value=None, key="report_to")

if st.button("📊 生成報告 Generate Report", type="primary", use_container_width=True):
    filters = {}
    if period_from:
        filters["date_from"] = str(period_from)
    if period_to:
        filters["date_to"] = str(period_to)

    receipts = get_receipts(company_id, filters)

    if receipts:
        df = pd.DataFrame(receipts)
        st.session_state.report_df = df
        st.session_state.report_receipts = receipts
        st.success(f"✅ 報告已生成 Report generated — {len(receipts)} receipts")
    else:
        st.warning("無數據 No data found for the selected period")

if "report_df" in st.session_state:
    df = st.session_state.report_df

    st.subheader("報告摘要 Report Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("收據數量 Receipts", len(df))
    with col2:
        total = df["total_amount"].sum() if "total_amount" in df.columns else 0
        st.metric("總金額 Total", f"HK${total:,.2f}")
    with col3:
        tax = df["tax_amount"].sum() if "tax_amount" in df.columns else 0
        st.metric("總稅款 Total Tax", f"HK${tax:,.2f}")

    st.divider()

    if "receipt_type" in df.columns:
        st.subheader("按類別 By Category")
        category_summary = df.groupby("receipt_type")["total_amount"].agg(["sum", "count"]).reset_index()
        category_summary.columns = ["Category", "Total (HKD)", "Count"]
        st.dataframe(category_summary, use_container_width=True, hide_index=True)

        st.bar_chart(category_summary, x="Category", y="Total (HKD)")

    st.divider()

    if "merchant_name" in df.columns:
        st.subheader("按商戶 By Merchant")
        merchant_summary = df.groupby("merchant_name")["total_amount"].agg(["sum", "count"]).reset_index()
        merchant_summary.columns = ["Merchant", "Total (HKD)", "Count"]
        st.dataframe(merchant_summary, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("下載 Download")
    excel_data = generate_excel_report(st.session_state.report_receipts)
    if excel_data:
        filename = f"receipt_report_{date.today().isoformat()}.xlsx"
        st.download_button(
            label="📥 下載 Excel Download Excel",
            data=excel_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    csv_data = generate_csv_report(st.session_state.report_receipts)
    if csv_data:
        csv_filename = f"receipt_report_{date.today().isoformat()}.csv"
        st.download_button(
            label="📄 下載 CSV Download CSV",
            data=csv_data,
            file_name=csv_filename,
            mime="text/csv",
            use_container_width=True,
        )
