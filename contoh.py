import streamlit as st
import requests
from datetime import datetime, timezone
import re
import math
import folium
from streamlit_folium import st_folium

# =====================================
# ⚙️ PAGE CONFIG
# =====================================
st.set_page_config(
    page_title="LANUD RSN Tactical METOC",
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
    mode = st.radio("Mode", ["OPS", "BRIEFING"])
    tz_mode = st.radio("Zona Waktu", ["UTC", "WIB"])

# =====================================
# 🔄 NATIVE AUTO REFRESH (SAFE)
# =====================================
if auto_refresh:
    st.markdown(
        f"<meta http-equiv='refresh' content='{refresh_min * 60}'>",
        unsafe_allow_html=True
    )

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
# 🧠 PARSING & WARNING
# =====================================
def extract_wind(metar):
    m = re.search(r'(\d{3})(\d{2})KT', metar)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None

def weather_warning(metar):
    warn = []

    if "TS" in metar or "CB" in metar:
        warn.append("⛈️ Thunderstorm / CB")
    if "RA" in metar:
        warn.append("🌧️ Rain Impact")
    if "FG" in metar or "BR" in metar:
        warn.append("🌫️ Low Visibility")

    _, ws = extract_wind(metar)
    if ws and ws >= 20:
        warn.append("💨 Strong Wind")

    if not warn:
        return "🟢 NORMAL", "green", ["No significant weather"]

    level = "🟡 CAUTION" if len(warn) == 1 else "🔴 WARNING"
    color = "orange" if level == "🟡 CAUTION" else "red"
    return level, color, warn

# =====================================
# ✈️ RUNWAY WIND COMPONENT
# =====================================
def runway_wind(wind_dir, wind_spd, rwy_heading):
    angle = math.radians(wind_dir - rwy_heading)
    head = round(wind_spd * math.cos(angle), 1)
    cross = round(wind_spd * math.sin(angle), 1)
    return head, cross

# =====================================
# 🧾 MAIN DISPLAY
# =====================================
st.title("✈️ Tactical METOC Dashboard")
st.subheader("Lanud Roesmin Nurjadin (WIBB)")

try:
    data = fetch_metar_taf()
    metar = next(d for d in data if d.startswith("METAR"))
    taf = next(d for d in data if d.startswith("TAF"))

    status, color, warnings = weather_warning(metar)

    # STATUS BAR
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

    # METAR / TAF
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📝 METAR")
        st.code(metar)

    with col2:
        st.markdown("### 📅 TAF")
        st.code(taf)

    # =====================================
    # 🌬️ WIND ANALYSIS
    # =====================================
    st.divider()
    st.markdown("## 🌬️ Runway Wind Analysis")

    wd, ws = extract_wind(metar)
    if wd:
        rwy18 = runway_wind(wd, ws, 180)
        rwy36 = runway_wind(wd, ws, 360)

        c1, c2 = st.columns(2)
        with c1:
            st.metric("RWY 18 Head/Tailwind", f"{rwy18[0]} kt")
            st.metric("RWY 18 Crosswind", f"{abs(rwy18[1])} kt")

        with c2:
            st.metric("RWY 36 Head/Tailwind", f"{rwy36[0]} kt")
            st.metric("RWY 36 Crosswind", f"{abs(rwy36[1])} kt")
    else:
        st.info("Wind data not available")

    # =====================================
    # 🛰️ SATELLITE & RADAR
    # =====================================
    st.divider()
    st.markdown("## 🛰️ Satellite & Radar")

    s1, s2 = st.columns(2)
    with s1:
        st.image(
            "https://rammb-slider.cira.colostate.edu/data/imagery/latest/himawari-9/full_disk/ir/00/000_000.png",
            caption="Himawari-9 IR – Cloud Top Temperature",
            use_column_width=True
        )

    with s2:
        st.image(
            "https://tilecache.rainviewer.com/v2/radar/nowcast.png",
            caption="Global Rain Radar (RainViewer)",
            use_column_width=True
        )

    # =====================================
    # 🗺️ TACTICAL MAP
    # =====================================
    st.divider()
    st.markdown("## 🗺️ Tactical Area Map (50 NM)")

    lanud_lat = 0.460
    lanud_lon = 101.444

    m = folium.Map(location=[lanud_lat, lanud_lon], zoom_start=8)
    folium.Marker(
        [lanud_lat, lanud_lon],
        popup="Lanud Roesmin Nurjadin",
        icon=folium.Icon(icon="plane", prefix="fa")
    ).add_to(m)

    folium.Circle(
        radius=92600,
        location=[lanud_lat, lanud_lon],
        color="blue",
        fill=False
    ).add_to(m)

    st_folium(m, use_container_width=True, height=400)

    # =====================================
    # 🕒 TIME
    # =====================================
    now_utc = datetime.now(timezone.utc)
    if tz_mode == "WIB":
        now = now_utc.astimezone(timezone.utc).replace(hour=(now_utc.hour + 7) % 24)
        tz = "WIB"
    else:
        now = now_utc
        tz = "UTC"

    st.caption(
        f"🕒 Last Update: {now.strftime('%Y-%m-%d %H:%M:%S')} {tz} | "
        f"Mode: {mode} | Refresh: {refresh_min} min"
    )

except Exception as e:
    st.error(f"❌ Error fetching weather data: {e}")
