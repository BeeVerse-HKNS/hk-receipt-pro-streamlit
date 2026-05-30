import streamlit as st
from datetime import date
from lib.supabase_client import create_receipt, upload_receipt_image, get_current_user
from lib.ocr_engine import extract_receipt_data, is_image_file

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
TYPE_LABELS = [RECEIPT_TYPES[k] for k in TYPE_KEYS]

if not st.session_state.get("logged_in"):
    st.warning("請先登入 Please login first")
    st.stop()

user = get_current_user()
company_id = st.session_state.company_id

st.title("📷 Upload Receipt")

tab_upload, tab_camera = st.tabs(["上傳檔案 Upload File", "拍照 Camera"])

uploaded_files = None
image_bytes = None
filename = None

with tab_upload:
    uploaded_files = st.file_uploader(
        "選擇收據檔案 Choose receipt files",
        type=["jpg", "jpeg", "png", "heic", "bmp", "tiff", "tif", "webp", "pdf", "docx", "doc", "xls", "xlsx", "csv", "txt"],
        key="file_uploader",
        accept_multiple_files=True,
    )
    if uploaded_files:
        if len(uploaded_files) == 1:
            image_bytes = uploaded_files[0].read()
            filename = uploaded_files[0].name
        else:
            st.info(f"📎 已選擇 {len(uploaded_files)} 個檔案 {len(uploaded_files)} files selected")

with tab_camera:
    camera_photo = st.camera_input("拍攝收據 Take a photo of receipt", key="camera")
    if camera_photo:
        image_bytes = camera_photo.read()
        filename = f"camera_{date.today().isoformat()}.jpg"

is_batch = uploaded_files is not None and len(uploaded_files) > 1

if is_batch:
    if st.button("🔍 批量 OCR 辨識 Process All OCR", type="primary", use_container_width=True):
        progress_bar = st.progress(0, text="辨識中 Processing...")
        batch_results = []
        total_amount = 0.0
        success_count = 0
        fail_count = 0

        for i, f in enumerate(uploaded_files):
            try:
                file_bytes = f.read()
                ocr_result = extract_receipt_data(file_bytes, f.name)
                image_url = upload_receipt_image(file_bytes, f.name, company_id)

                receipt_data = {
                    "merchant_name": ocr_result.get("merchant", ""),
                    "receipt_date": str(ocr_result.get("date", date.today())),
                    "total_amount": float(ocr_result.get("total", 0.0)),
                    "tax_amount": float(ocr_result.get("tax", 0.0)),
                    "receipt_type": ocr_result.get("type", "miscellaneous"),
                    "description": ocr_result.get("description", ""),
                    "payment_method": ocr_result.get("payment_method", "N/A"),
                    "notes": "",
                    "image_url": image_url,
                    "company_id": company_id,
                    "user_id": st.session_state.user_id,
                    "status": "draft",
                }

                result = create_receipt(receipt_data)
                if result:
                    success_count += 1
                    total_amount += float(ocr_result.get("total", 0.0))
                else:
                    fail_count += 1

                batch_results.append({
                    "filename": f.name,
                    "ocr_result": ocr_result,
                    "saved": result is not None,
                })
            except Exception:
                fail_count += 1
                batch_results.append({
                    "filename": f.name,
                    "ocr_result": {},
                    "saved": False,
                })

            progress_bar.progress(
                (i + 1) / len(uploaded_files),
                text=f"辨識中 Processing... ({i + 1}/{len(uploaded_files)})",
            )

        progress_bar.empty()

        st.divider()
        st.subheader("📊 批量處理摘要 Batch Summary")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("總檔案 Total Files", len(uploaded_files))
        with c2:
            st.metric("成功 Success", success_count)
        with c3:
            st.metric("失敗 Failed", fail_count)
        with c4:
            st.metric("總金額 Total Amount", f"HK${total_amount:,.2f}")

        st.divider()
        st.subheader("📋 處理結果 Results")
        for br in batch_results:
            ocr = br["ocr_result"]
            status_icon = "✅" if br["saved"] else "❌"
            merchant = ocr.get("merchant", "Unknown")
            r_date = ocr.get("date", "N/A")
            r_total = ocr.get("total", 0.0)
            r_type = ocr.get("type", "miscellaneous")
            type_label = RECEIPT_TYPES.get(r_type, r_type)

            with st.expander(f"{status_icon} {br['filename']} — {merchant}"):
                st.write(f"**商戶 Merchant:** {merchant}")
                st.write(f"**日期 Date:** {r_date}")
                st.write(f"**金額 Total:** HK${r_total:,.2f}")
                st.write(f"**類型 Type:** {type_label}")
                st.write(f"**描述 Description:** {ocr.get('description', '')}")
                st.write(f"**付款方式 Payment:** {ocr.get('payment_method', 'N/A')}")

elif image_bytes:
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

if "ocr_result" in st.session_state and not is_batch:
    ocr_result = st.session_state.ocr_result

    st.divider()
    st.subheader("收據資料 Receipt Details")

    m_val = ocr_result.get("merchant", "")
    d_val = ocr_result.get("date", date.today())
    t_val = ocr_result.get("total", 0.0)
    ty_val = ocr_result.get("type", "miscellaneous")
    desc_val = ocr_result.get("description", "")
    pay_val = ocr_result.get("payment_method", "N/A")

    ci1 = "✅" if m_val else "⚠️"
    ci2 = "✅" if d_val else "⚠️"
    ci3 = "✅" if t_val and t_val > 0 else "⚠️"
    ci4 = "✅" if ty_val else "⚠️"
    ci5 = "✅" if desc_val else "⚠️"
    ci6 = "✅" if pay_val and pay_val != "N/A" else "⚠️"

    type_index = TYPE_KEYS.index(ty_val) if ty_val in TYPE_KEYS else TYPE_KEYS.index("miscellaneous")

    with st.form("receipt_form"):
        col1, col2 = st.columns(2)

        with col1:
            merchant = st.text_input(f"{ci1} 商戶名稱 Merchant", value=m_val)
            receipt_date = st.date_input(f"{ci2} 日期 Date", value=d_val)
            receipt_type = st.selectbox(
                f"{ci4} 收據類型 Type",
                TYPE_KEYS,
                index=type_index,
                format_func=lambda x: RECEIPT_TYPES[x],
            )

        with col2:
            total_amount = st.number_input(
                f"{ci3} 總金額 Total (HKD)",
                min_value=0.0,
                value=float(t_val),
                step=0.1,
            )
            description = st.text_input(f"{ci5} 描述 Description", value=desc_val)
            payment_method = st.text_input(f"{ci6} 付款方式 Payment Method", value=pay_val)
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
                    "tax_amount": 0.0,
                    "receipt_type": receipt_type,
                    "description": description,
                    "payment_method": payment_method,
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
