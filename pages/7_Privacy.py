import streamlit as st
from lib.supabase_client import export_user_data, request_account_deletion, get_current_user

if not st.session_state.get("logged_in"):
    st.warning("請先登入 Please login first")
    st.stop()

user = get_current_user()

st.title("🔒 Privacy Policy 私隱政策")

st.markdown("""
## 《個人資料（私隱）條例》PDPO Compliance Notice

### 資料收集目的 Data Collection Purpose

HK Receipt Pro 收集以下個人資料用於：

1. **帳戶管理** — 電郵地址用於登入及帳戶識別
2. **收據管理** — 收據圖片及資料用於 expense tracking 及報告生成
3. **審批流程** — 提交及審批記錄用於公司內部報銷流程
4. **合規報告** — 匯總數據用於稅務及審計用途

### 資料保存 Data Retention

- 收據圖片及資料保存至用戶刪除或帳戶終止
- 審批記錄保存 7 年（符合香港稅務法規）
- 帳戶資料於刪除請求後 30 日內移除

### 資料安全 Data Security

- 所有數據傳輸使用 TLS 加密
- 數據庫啟用 Row Level Security (RLS)
- 收據圖片存儲於私有 Storage Bucket
- 僅授權人員可訪問數據

### 資料使用者權利 Data Subject Rights

根據 PDPO 第 6 條，你有權：

1. ✅ 查閱你的個人資料
2. ✅ 要求更正不準確的資料
3. ✅ 匯出所有個人數據
4. ✅ 要求刪除個人數據

### 跨境數據傳輸 Cross-border Data Transfer

數據存儲於 Supabase（亞太區伺服器）。如需跨境傳輸，將確保符合 PDPO 第 33 條規定。

---

## 數據操作 Data Actions
""")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("📤 匯出數據 Export Data")
    st.write("下載你的所有個人資料及收據記錄")
    if st.button("匯出我的數據 Export My Data", use_container_width=True, type="primary"):
        with st.spinner("匯出中 Exporting..."):
            data = export_user_data(st.session_state.user_id)
        if data:
            st.success("✅ 數據已準備 Data exported!")
            st.json(data)
        else:
            st.error("匯出失敗 Export failed")

with col2:
    st.subheader("🗑️ 刪除帳戶 Delete Account")
    st.write("⚠️ 此操作不可逆 — 所有數據將被永久刪除")
    st.warning("刪除後 30 日內完成，期間可聯絡管理員取消")
    confirm = st.checkbox("我了解此操作不可逆 I understand this is irreversible")
    if st.button("申請刪除帳戶 Request Account Deletion", use_container_width=True, disabled=not confirm):
        with st.spinner("處理中 Processing..."):
            result = request_account_deletion(st.session_state.user_id)
        if result:
            st.success("✅ 刪除請求已提交 Deletion request submitted. You will be notified within 30 days.")
        else:
            st.error("請求失敗 Request failed")
