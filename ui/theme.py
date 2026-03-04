def apply_theme():

    import streamlit as st

    st.markdown("""
    <style>

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1a1a1a;
    }

    .stApp {
        background: linear-gradient(
            135deg,
            #fff1f5,
            #fff7ed,
            #f8fafc
        );
    }

    .topbar {
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 70%;
        height: 60px;
        background: rgba(255,255,255,0.8);
        backdrop-filter: blur(12px);
        border-radius: 18px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.08);
        display: flex;
        align-items: center;
        padding-left: 30px;
        font-weight: 600;
        font-size: 20px;
        z-index: 9999;
    }

    section[data-testid="stSidebar"] {
        top: 120px;
        left: 20px;
        border-radius: 18px;
        background: white;
        box-shadow: 0 10px 40px rgba(0,0,0,0.08);
    }

    .card {
        background: white;
        padding: 30px;
        border-radius: 22px;
        box-shadow: 0 10px 35px rgba(0,0,0,0.06);
        margin-bottom: 25px;
    }

    textarea, input {
        border-radius: 12px !important;
        border: 1px solid #e5e7eb !important;
        padding: 10px !important;
    }

    .stButton>button {
        background: linear-gradient(135deg,#ff6f91,#ff9671);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 12px 24px;
        font-weight: 600;
        width: 100%;
    }

    .user-msg {
        background:#ff6f91;
        color:white;
        padding:10px 14px;
        border-radius:14px;
        margin:6px;
        width:fit-content;
        margin-left:auto;
    }

    .bot-msg {
        background:#f3f4f6;
        padding:10px 14px;
        border-radius:14px;
        margin:6px;
        width:fit-content;
    }

    </style>
    """, unsafe_allow_html=True)