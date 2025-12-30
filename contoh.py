import streamlit as st
import requests
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh

# =====================================
# ⚙️ PAGE CONFIG
# =====================================
st.set_page_config(
    page_title="LANUD RSN Tactical Weather",
    page_icon="✈️",
    layout="wide"
)

# =====================================
# 🌐 DATA SOURCE
# =====================================
METAR_TAF_URL = "https://aviationweather.gov/api/data/metar"

# =====================================
# 🔁 AUTO REFRESH CONTROL
# =====================================
with st.sidebar:
    st.markdown("## ⚙️ Control Panel")
    refresh_minutes = st.slider("Auto Refresh (menit)", 1, 30, 5)
    auto_refresh = st.toggle("Auto Refresh", True)
    timezone_mode = st.radio("Zona Waktu", ["UTC", "WIB"])

if auto_refresh:
    st_autorefresh(interval=refresh_minutes * 60 * 1000, key="auto_refresh")

# =====================================
# 📡 FETCH DATA
# =====================================
def fetch_metar_taf():
    params = {
        "ids": "WIBB",
        "hours": 0,
        "sep": "true",
        "taf": "true"
    }
    r = requests.get(METAR_TAF_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.text.strip().split("\n")

# =====================================
# 🧠 FLIGHT CONDITION LOGIC (SIMPLE)
# =====================================
def assess_flight_condition(metar):
    if any(x in metar for x in ["TS", "RA", "FG", "BKN", "OVC"]):
        return "🔴 IMC / RESTRICTED", "red"
    if "SCT" in metar:
        return "🟡 MARGINAL VMC", "orange"
    return "🟢 VMC / GO", "green"

# =====================================
# 🧾 MAIN
# =====================================
st.title("✈️ Tactical Weather Briefing")
st.subheader("Lanud Roesmin Nurjadin (WIBB)")

try:
    data = fetch_metar_taf()
    metar = next((d for d in data if d.startswith("METAR")), "METAR tidak tersedia")
    taf = next((d for d in data if d.startswith("TAF")), "TAF tidak tersedia")

    status, color = assess_flight_condition(metar)

    # ================================
    # 🚦 STATUS BAR
    # ================================
    st.markdown(
        f"""
        <div style="padding:10px;border-radius:8px;background-color:{color};color:white;font-weight:bold;">
        FLIGHT STATUS: {status}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # ================================
    # 📊 DATA DISPLAY
    # ================================
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📝 METAR (Observasi)")
        st.code(metar, language="text")

    with col2:
        st.markdown("### 📅 TAF (Forecast)")
        st.code(taf, language="text")

    # ================================
    # 🕒 UPDATE TIME
    # ================================
    now_utc = datetime.now(timezone.utc)
    if timezone_mode == "WIB":
        now = now_utc.astimezone(timezone.utc).replace(hour=(now_utc.hour + 7) % 24)
        tz_label = "WIB"
    else:
        now = now_utc
        tz_label = "UTC"

    st.divider()
    st.caption(
        f"🕒 Last Update: {now.strftime('%Y-%m-%d %H:%M:%S')} {tz_label} | "
        f"Auto Refresh: {refresh_minutes} menit"
    )

except Exception as e:
    st.error(f"❌ Gagal mengambil data cuaca: {e}")
