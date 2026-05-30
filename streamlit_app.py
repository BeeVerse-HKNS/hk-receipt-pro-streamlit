import streamlit as st
from lib.supabase_client import sign_in, sign_up, sign_out, get_current_user

st.set_page_config(
    page_title="HK Receipt Pro",
    page_icon="🧾",
    layout="wide",
)

st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #1a1a2e;
    }
    [data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }
    .login-container {
        max-width: 420px;
        margin: 4rem auto;
        padding: 2.5rem;
        border-radius: 12px;
        background: #ffffff;
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    }
    .login-title {
        text-align: center;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .login-subtitle {
        text-align: center;
        color: #888;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        padding: 0.6rem 1rem;
    }
    div[data-testid="stForm"] {
        border: none;
        padding: 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    defaults = {
        "logged_in": False,
        "user_id": None,
        "email": None,
        "role": None,
        "company_id": None,
        "supabase_client": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def show_login_page():
    tab_login, tab_register = st.tabs(["登入 Login", "註冊 Register"])

    with tab_login:
        with st.form("login_form"):
            st.markdown('<div class="login-title">🧾 HK Receipt Pro</div>', unsafe_allow_html=True)
            st.markdown('<div class="login-subtitle">香港中小企收據管理系統</div>', unsafe_allow_html=True)
            email = st.text_input("電郵 Email", placeholder="admin@company.com.hk")
            password = st.text_input("密碼 Password", type="password")
            submitted = st.form_submit_button("登入 Login", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.error("請填寫所有欄位 Please fill in all fields")
                    return
                result = sign_in(email, password)
                if result and result.get("user"):
                    user = result["user"]
                    st.session_state.logged_in = True
                    st.session_state.user_id = user.id
                    st.session_state.email = user.email
                    st.session_state.role = result.get("profile", {}).get("role", "employee")
                    st.session_state.company_id = result.get("profile", {}).get("company_id")
                    st.rerun()
                else:
                    st.error("登入失敗 Login failed — please check your credentials")

    with tab_register:
        with st.form("register_form"):
            st.markdown("### 註冊新公司 Register New Company")
            company_name = st.text_input("公司名稱 Company Name", placeholder="ABC Trading Ltd.")
            admin_email = st.text_input("管理員電郵 Admin Email", placeholder="admin@company.com.hk")
            admin_password = st.text_input("密碼 Password", type="password")
            confirm_password = st.text_input("確認密碼 Confirm Password", type="password")
            pdpo_consent = st.checkbox(
                "我同意《個人資料（私隱）條例》PDPO — I consent to data collection under PDPO"
            )
            submitted = st.form_submit_button("註冊 Register", use_container_width=True)

            if submitted:
                if not all([company_name, admin_email, admin_password, confirm_password]):
                    st.error("請填寫所有欄位 Please fill in all fields")
                    return
                if admin_password != confirm_password:
                    st.error("密碼不一致 Passwords do not match")
                    return
                if not pdpo_consent:
                    st.error("必須同意 PDPO Consent is required")
                    return
                if len(admin_password) < 8:
                    st.error("密碼至少 8 位 Password must be at least 8 characters")
                    return
                result = sign_up(admin_email, admin_password, company_name)
                if result and result.get("user"):
                    st.success("註冊成功！Registration successful! Please login.")
                else:
                    error_msg = result.get("error", "Registration failed") if result else "Registration failed"
                    st.error(f"註冊失敗 {error_msg}")


def show_main_app():
    with st.sidebar:
        st.markdown(f"**{st.session_state.email}**")
        st.caption(f"角色 Role: {st.session_state.role}")
        if st.button("登出 Logout", use_container_width=True):
            sign_out()
            st.rerun()

    pg = st.navigation([
        st.Page("pages/1_Dashboard.py", title="Dashboard", icon="📊"),
        st.Page("pages/2_Upload.py", title="Upload", icon="📷"),
        st.Page("pages/3_Receipts.py", title="Receipts", icon="🧾"),
        st.Page("pages/4_Reports.py", title="Reports", icon="📈"),
        st.Page("pages/5_Admin.py", title="Admin", icon="⚙️"),
        st.Page("pages/6_Guide.py", title="Guide", icon="📖"),
        st.Page("pages/7_Privacy.py", title="Privacy", icon="🔒"),
    ])
    pg.run()


def main():
    init_session_state()
    if st.session_state.logged_in:
        show_main_app()
    else:
        show_login_page()


if __name__ == "__main__":
    main()
