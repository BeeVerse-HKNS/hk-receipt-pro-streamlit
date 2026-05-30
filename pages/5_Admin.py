import streamlit as st
from lib.supabase_client import (
    list_employees,
    invite_employee,
    get_pending_approvals,
    approve_receipt,
    reject_receipt,
    get_current_user,
)

if not st.session_state.get("logged_in"):
    st.warning("請先登入 Please login first")
    st.stop()

user = get_current_user()

if st.session_state.role not in ("admin", "manager"):
    st.error("⛔ 權限不足 Access denied — Admin/Manager only")
    st.stop()

company_id = st.session_state.company_id

st.title("⚙️ Admin")

tab_employees, tab_approvals = st.tabs(["👥 員工 Employees", "✅ 審批 Approvals"])

with tab_employees:
    st.subheader("員工列表 Employee List")
    employees = list_employees(company_id)
    if employees:
        for emp in employees:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{emp.get('email', 'N/A')}**")
            with col2:
                st.write(f"角色: {emp.get('role', 'N/A')}")
            with col3:
                st.write(f"狀態: {'✅' if emp.get('active', True) else '❌'}")
    else:
        st.info("暫無員工 No employees found")

    st.divider()

    st.subheader("邀請員工 Invite Employee")
    with st.form("invite_form"):
        inv_email = st.text_input("電郵 Email", placeholder="employee@company.com.hk")
        inv_role = st.selectbox("角色 Role", ["employee", "manager"])
        invited = st.form_submit_button("📤 邀請 Invite", use_container_width=True)

        if invited:
            if not inv_email:
                st.error("請填寫電郵 Email is required")
            else:
                result = invite_employee(inv_email, inv_role, company_id)
                if result:
                    st.success(f"✅ 已邀請 {inv_email}")
                else:
                    st.error("邀請失敗 Invite failed")

with tab_approvals:
    st.subheader("待審批收據 Pending Approvals")
    pending = get_pending_approvals(company_id)

    if pending:
        for r in pending:
            receipt_label = f"{r.get('merchant_name', 'Unknown')} — HK${r.get('total_amount', 0):,.2f} by {r.get('submitted_by_email', 'Unknown')}"
            with st.expander(receipt_label):
                col_info, col_actions = st.columns([2, 1])

                with col_info:
                    st.write(f"**日期 Date:** {r.get('receipt_date', 'N/A')}")
                    st.write(f"**類型 Type:** {r.get('receipt_type', 'N/A')}")
                    st.write(f"**稅款 Tax:** HK${r.get('tax_amount', 0):,.2f}")
                    st.write(f"**備註 Notes:** {r.get('notes', '')}")
                    st.write(f"**提交人 Submitted by:** {r.get('submitted_by_email', 'N/A')}")

                with col_actions:
                    if st.button("✅ 批准 Approve", key=f"approve_{r.get('id', '')}", type="primary"):
                        result = approve_receipt(r["id"], st.session_state.user_id)
                        if result:
                            st.success("已批准 Approved!")
                            st.rerun()
                        else:
                            st.error("批准失敗 Approve failed")

                    reject_key = f"reject_{r.get('id', '')}"
                    reject_reason = st.text_input("拒絕原因 Reason", key=f"reason_{r.get('id', '')}")
                    if st.button("❌ 拒絕 Reject", key=reject_key):
                        if not reject_reason:
                            st.error("請填寫拒絕原因 Reason is required")
                        else:
                            result = reject_receipt(r["id"], st.session_state.user_id, reject_reason)
                            if result:
                                st.success("已拒絕 Rejected!")
                                st.rerun()
                            else:
                                st.error("拒絕失敗 Reject failed")
    else:
        st.info("暫無待審批收據 No pending approvals")
