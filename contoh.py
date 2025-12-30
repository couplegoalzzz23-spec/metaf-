import streamlit as st
import requests
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh
import re

# =====================================
# ⚙️ PAGE CONFIG
# =====================================
st.set_page_config(
    page_title="LANUD RSN METOC Dashboard",
    page_icon="✈️",
    layout="wide"
)

# =====================================
# 🔁 SIDEBAR CONTROL
# =====================================
with st.sidebar:
    st.markdown("## ⚙️ OPS CONTROL")
    refresh_min = st.slider("Auto Refresh (menit)", 1, 30, 5)
    auto_refresh = st.toggle("Auto Refresh", True)
    view_mode = st.radio("Mode Tampilan", ["OPS", "BRIEFING"])
    tz_mode = st.radio("Zona Waktu", ["UTC", "WIB"])

if auto_refresh:
    st_autorefresh(interval=refresh_min * 60 * 1000, key="refresh")

# =====================================
# 🌐 DATA SOURCE
# =====================================
METAR_URL = "https://aviationweather.gov/api/data/metar"

def fetch_metar_taf():
    params = {
        "ids": "WIBB",
        "hours": 0,
        "sep": "true",
        "taf": "true"
    }
    r = requests.get(METAR_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.text.strip().split("\n")

# =====================================
# ⚠️ WEATHER WARNING LOGIC
# =====================================
def weather_warning(metar):
    warnings = []

    if "TS" in metar or "CB" in metar:
        warnings.append("⛈️ THUNDERSTORM / CB")
    if "RA" in metar:
        warnings.append("🌧️ RAIN IMPACT")
    if "FG" in metar or "BR" in metar:
        warnings.append("🌫️ LOW VISIBILITY")

    wind = re.search(r'(\d{2})KT', metar)
    if wind and int(wind.group(1)) >= 20:
        warnings.append("💨 STRONG WIND")

    if not warnings:
        return "🟢 NORMAL", "green", ["No significant weather"]

    level = "🟡 CAUTION" if len(warnings) == 1 else "🔴 WARNING"
    color = "orange" if level == "🟡 CAUTION" else "red"

    return level, color, warnings

# =====================================
# 🧾 MAIN
# =====================================
st.title("✈️ Tactical METOC Dashboard")
st.subheader("Lanud Roesmin Nurjadin (WIBB)")

try:
    data = fetch_metar_taf()
    metar = next((d for d in data if d.startswith("METAR")), "METAR N/A")
    taf = next((d for d in data if d.startswith("TAF")), "TAF N/A")

    status, color, warnings = weather_warning(metar)

    # =====================================
    # 🚦 STATUS BAR
    # =====================================
    st.markdown(
        f"""
        <div style="padding:12px;border-radius:8px;
        background-color:{color};color:white;font-size:18px;font-weight:bold;">
        FLIGHT STATUS: {status}
        </div>
        """,
        unsafe_allow_html=True
    )

    for w in warnings:
        st.warning(w)

    st.divider()

    # =====================================
    # 📝 METAR & TAF
    # =====================================
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📝 METAR (Observasi)")
        st.code(metar, language="text")

    with col2:
        st.markdown("### 📅 TAF (Prakiraan)")
        st.code(taf, language="text")

    # =====================================
    # 🛰️ SATELLITE & RADAR
    # =====================================
    st.divider()
    st.markdown("## 🛰️ Satellite & Radar")

    sat_col, rad_col = st.columns(2)

    with sat_col:
        st.markdown("### 🌍 Himawari-9 IR (Asia)")
        st.image(
            "https://rammb-slider.cira.colostate.edu/data/imagery/2023/09/21/himawari-9/full_disk/ir/00/000_000.png",
            caption="Infrared Satellite – Cloud Top Temperature",
            use_column_width=True
        )

    with rad_col:
        st.markdown("### 🌧️ Rain Radar (Global)")
        st.image(
            "https://tilecache.rainviewer.com/v2/radar/nowcast.png",
            caption="Precipitation Radar (RainViewer)",
            use_column_width=True
        )

    # =====================================
    # 🕒 TIME INFO
    # =====================================
    now_utc = datetime.now(timezone.utc)
    if tz_mode == "WIB":
        now = now_utc.astimezone(timezone.utc).replace(hour=(now_utc.hour + 7) % 24)
        tz = "WIB"
    else:
        now = now_utc
        tz = "UTC"

    st.divider()
    st.caption(
        f"🕒 Last Update: {now.strftime('%Y-%m-%d %H:%M:%S')} {tz} | "
        f"Refresh: {refresh_min} menit | Mode: {view_mode}"
    )

except Exception as e:
    st.error(f"❌ Data fetch error: {e}")
