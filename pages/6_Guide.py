import streamlit as st

if not st.session_state.get("logged_in"):
    st.warning("請先登入 Please login first")
    st.stop()

st.title("📖 User Guide 使用指南")

st.markdown("""
## 🚀 快速開始 Quick Start

### 1. 上傳收據 Upload a Receipt
- 前往 **Upload** 頁面
- 選擇上傳圖片或使用相機拍照
- 點擊 **OCR 辨識** 自動提取收據資料
- 核對並編輯資料後點擊 **儲存**

### 2. 查看收據 View Receipts
- 前往 **Receipts** 頁面查看所有收據
- 使用篩選器按日期、商戶、類型或狀態搜尋
- 點擊展開收據詳情，可編輯或提交審批

### 3. 提交審批 Submit for Approval
- 在收據詳情中點擊 **Submit for Approval**
- 管理員將在 **Admin** 頁面看到待審批收據
- 審批結果會更新收據狀態

### 4. 生成報告 Generate Reports
- 前往 **Reports** 頁面
- 選擇日期範圍並點擊 **Generate Report**
- 可下載 Excel 格式報告

---

## 🧾 支援的香港收據類型 Supported HK Receipt Types

| 類型 Type | 說明 Description | 常見商戶 Examples |
|-----------|-----------------|------------------|
| 🛒 Retail | 零售購物 | Wellcome, ParknShop, 7-Eleven |
| 🍽️ Restaurant | 餐飲 | 茶餐廳, 快餐店, 酒樓 |
| 🚌 Transportation | 交通 | MTR, 巴士, 的士 |
| 💡 Utilities | 水電煤氣 | 中電, 港燈, 煤氣公司 |
| 📦 Other | 其他 | 辦公用品, 維修, 雜項 |

---

## ❓ 常見問題 FAQ

### Q: 支援哪些圖片格式？
A: 支援 JPG、PNG 及 HEIC 格式。

### Q: OCR 辨識準確嗎？
A: 系統使用 PaddleOCR 及 Tesseract 雙引擎，對中文及英文收據均有良好辨識率。建議上傳清晰、光線充足的圖片以獲得最佳效果。

### Q: 我的數據安全嗎？
A: 所有數據存儲於 Supabase，啟用 Row Level Security (RLS)。圖片存儲於私有 Storage Bucket，需認證才能訪問。系統符合香港《個人資料（私隱）條例》(PDPO)。

### Q: 如何刪除我的數據？
A: 前往 **Privacy** 頁面，可匯出或申請刪除所有個人數據。

### Q: 誰可以審批收據？
A: 只有 Admin 及 Manager 角色可以審批收據。

### Q: 報告可以匯出什麼格式？
A: 目前支援 Excel (.xlsx) 格式匯出。

### Q: 手機可以使用嗎？
A: 可以！Streamlit 支援流動瀏覽器，Upload 頁面提供相機拍照功能。
""")
