import streamlit as st
from datetime import date
from lib.supabase_client import create_receipt, upload_receipt_image, get_current_user
from lib.ocr_engine import extract_receipt_data, is_image_file

if not st.session_state.get("logged_in"):
    st.warning("請先登入 Please login first")
    st.stop()

user = get_current_user()
company_id = st.session_state.company_id

st.title("📷 Upload Receipt")

tab_upload, tab_camera = st.tabs(["上傳檔案 Upload File", "拍照 Camera"])

image_bytes = None
filename = None

with tab_upload:
    uploaded_file = st.file_uploader(
        "選擇收據檔案 Choose receipt file",
        type=["jpg", "jpeg", "png", "heic", "bmp", "tiff", "tif", "webp", "pdf", "docx", "doc", "xls", "xlsx", "csv", "txt"],
        key="file_uploader",
    )
    if uploaded_file:
        image_bytes = uploaded_file.read()
        filename = uploaded_file.name

with tab_camera:
    camera_photo = st.camera_input("拍攝收據 Take a photo of receipt", key="camera")
    if camera_photo:
        image_bytes = camera_photo.read()
        filename = f"camera_{date.today().isoformat()}.jpg"

if image_bytes:
    if is_image_file(filename or ""):
        st.image(image_bytes, caption="收據預覽 Receipt Preview", use_container_width=True)
    elif (filename or "").lower().endswith(".pdf"):
        st.info(f"📄 PDF 檔案已上傳 PDF file uploaded — {filename}")
    else:
        st.info(f"📎 檔案已上傳 File uploaded — {filename}")

    if st.button("🔍 OCR 辨識 Process OCR", type="primary", use_container_width=True):
        with st.spinner("辨識中 Processing..."):
            ocr_result = extract_receipt_data(image_bytes, filename)

        st.session_state.ocr_result = ocr_result
        st.success("辨識完成 OCR complete!")

if "ocr_result" in st.session_state:
    ocr_result = st.session_state.ocr_result

    st.divider()
    st.subheader("收據資料 Receipt Details")

    with st.form("receipt_form"):
        col1, col2 = st.columns(2)

        with col1:
            merchant = st.text_input("商戶名稱 Merchant", value=ocr_result.get("merchant", ""))
            receipt_date = st.date_input("日期 Date", value=ocr_result.get("date", date.today()))
            receipt_type = st.selectbox(
                "收據類型 Type",
                ["retail", "restaurant", "transportation", "utilities", "other"],
                index=["retail", "restaurant", "transportation", "utilities", "other"].index(
                    ocr_result.get("type", "other")
                ) if ocr_result.get("type") in ["retail", "restaurant", "transportation", "utilities", "other"] else 4,
            )

        with col2:
            total_amount = st.number_input(
                "總金額 Total (HKD)",
                min_value=0.0,
                value=float(ocr_result.get("total", 0.0)),
                step=0.1,
            )
            tax_amount = st.number_input(
                "稅款 Tax (HKD)",
                min_value=0.0,
                value=float(ocr_result.get("tax", 0.0)),
                step=0.1,
            )
            notes = st.text_area("備註 Notes", value="")

        submitted = st.form_submit_button("💾 儲存收據 Save Receipt", type="primary", use_container_width=True)

        if submitted:
            if not merchant:
                st.error("請填寫商戶名稱 Merchant name is required")
            elif total_amount <= 0:
                st.error("金額必須大於零 Amount must be greater than zero")
            else:
                image_url = None
                if image_bytes:
                    image_url = upload_receipt_image(image_bytes, filename, company_id)

                receipt_data = {
                    "merchant_name": merchant,
                    "receipt_date": str(receipt_date),
                    "total_amount": total_amount,
                    "tax_amount": tax_amount,
                    "receipt_type": receipt_type,
                    "notes": notes,
                    "image_url": image_url,
                    "company_id": company_id,
                    "user_id": st.session_state.user_id,
                    "status": "draft",
                }

                result = create_receipt(receipt_data)
                if result:
                    st.success("✅ 收據已儲存 Receipt saved!")
                    if "ocr_result" in st.session_state:
                        del st.session_state.ocr_result
                else:
                    st.error("儲存失敗 Failed to save receipt")
