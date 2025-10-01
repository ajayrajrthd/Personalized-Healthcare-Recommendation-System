import streamlit as st
from streamlit_lottie import st_lottie
import requests
from utils.db import init_db, ensure_default_users, set_password
from utils.auth import hash_password

# -------------------------
# Page Config
# -------------------------
st.set_page_config(page_title="Healthcare Recommender", page_icon="🩺", layout="wide")

# -------------------------
# Lottie loader
# -------------------------
def load_lottie(url: str):
    try:
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None

lottie_health = load_lottie("https://assets9.lottiefiles.com/packages/lf20_jcikwtux.json")
lottie_ai = load_lottie("https://assets7.lottiefiles.com/packages/lf20_q5pk6p1k.json")

# -------------------------
# Global CSS (Dark/Light adaptive)
# -------------------------
st.markdown(
    """
    <style>
    
    /* Button styles */
    .get-started-btn {
        display: flex;
        justify-content: center;
        margin: 30px 0;
    }
    .stButton>button {
        background-color: #007bff !important; /* Blue */
        color: white !important;
        border: none !important;
        padding: 12px 28px;
        font-size: 18px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #0056b3 !important; /* Darker Blue */
    }

    /* Text styles */
    .big-title {
        font-size: 35px !important;
        font-weight: 800;
        color: var(--text-color);
        text-align: center;
        margin-bottom: 6px;
    }
    .sub-title {
        font-size: 18px;
        color: var(--secondary-text-color);
        text-align: center;
        margin-top: 0;
        margin-bottom: 20px;
    }

    /* Dark/Light theme vars */
    :root {
        --bg-color: #ffffff;
        --card-bg: #f9f9f9;
        --text-color: #0b3d91;
        --secondary-text-color: #586e75;
        --border-color: rgba(12,40,80,0.08);
    }
    [data-testid="stAppViewContainer"] {
        background-color: var(--bg-color);
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-color: #0e1117;
            --card-bg: #1e222b;
            --text-color: #e5e7eb;
            --secondary-text-color: #9ca3af;
            --border-color: rgba(255,255,255,0.08);
        }
    }

    /* Feature card style */
    .feature-card {
        background: var(--card-bg);
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.12);
        transition: transform 0.16s ease, box-shadow 0.16s ease;
        border: 1px solid var(--border-color);
    }
    .feature-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 28px rgba(0,0,0,0.25);
    }
    .feature-card-inner {
        display:flex;
        gap:14px;
        align-items:flex-start;
    }
    .feature-card .icon {
        font-size: 34px;
        width:56px;
        height:56px;
        border-radius:12px;
        display:flex;
        align-items:center;
        justify-content:center;
        background: rgba(11,61,145,0.15);
        color: var(--text-color);
        flex-shrink:0;
    }
    .feature-card h3 {
        margin: 0 0 6px 0;
        font-size: 20px;
        color: var(--text-color);
    }
    .feature-card p {
        margin: 0;
        color: var(--secondary-text-color);
        line-height: 1.45;
    }

    /* Footer */
    .footer {
        text-align: center;
        font-size: 13px;
        color: var(--secondary-text-color);
        margin-top: 36px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Hero Section
# -------------------------
c1, c2 = st.columns([1, 2.7])
with c1:
    if lottie_health:
        st_lottie(lottie_health, height=200, key="lhealth")
with c2:
    st.markdown('<div class="big-title">🩺 Personalized Healthcare Recommendation System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Smart, data-driven, and privacy-conscious — AI-powered suggestions for better health outcomes</div>', unsafe_allow_html=True)

st.markdown("---")

# -------------------------
# Feature cards
# -------------------------
st.subheader("✨ Key Features")
col_left, col_right = st.columns(2, gap="large")

# Left cards
with col_left:
    st.markdown("""
    <div class="feature-card feature-stack">
      <div class="feature-card-inner">
        <div class="icon">📋</div>
        <div>
          <h3>Personalized Recommendations</h3>
          <p>Tailored healthcare suggestions that adapt to user context and preferences.</p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-card feature-stack">
      <div class="feature-card-inner">
        <div class="icon">🧪</div>
        <div>
          <h3>Disease Prediction</h3>
          <p>Predict possible health conditions from symptoms using machine learning models.</p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# Right cards
with col_right:
    st.markdown("""
    <div class="feature-card feature-stack">
      <div class="feature-card-inner">
        <div class="icon">💊</div>
        <div>
          <h3>Medicine Recommendation</h3>
          <p>Receive medicine suggestions linked with conditions and graph-based knowledge insights.</p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-card feature-stack">
      <div class="feature-card-inner">
        <div class="icon">📊</div>
        <div>
          <h3>Analytics Dashboard</h3>
          <p>Track activity and engagement through interactive dashboards with detailed metrics.</p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# -------------------------
# CTA Button (Go to Login/Signup)
# -------------------------
col_center = st.columns([1, 1, 1])
with col_center[1]:
    if st.button(" Get Started", use_container_width=True):
        st.switch_page("pages/1_👤_Login_Signup.py")  # 👈 Update path if your login page filename differs


# -------------------------
# Footer
# -------------------------
st.markdown('<div class="footer">⚠️ Demo only — synthetic data. Not a medical device. For clinical decisions consult a professional.</div>', unsafe_allow_html=True)

# -------------------------
# DB init & demo users
# -------------------------
try:
    init_db()
    ensure_default_users()
    set_password("admin@demo.com", hash_password("admin123"))
    set_password("analyst@demo.com", hash_password("analyst123"))
    set_password("user@demo.com", hash_password("user123"))
except Exception:
    pass
