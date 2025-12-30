import streamlit as st
import requests
import time
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="WIBB Live Weather", page_icon="✈️", layout="wide")

def fetch_weather_data():
    url = "https://aviationweather.gov/api/data/metar?ids=WIBB&hours=0&sep=true&taf=true"
    try:
        # Menambahkan parameter acak agar tidak terkena cache browser/server
        response = requests.get(url, params={'t': time.time()})
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error: {e}"

# --- LOGIKA AUTO REFRESH ---
# Interval dalam detik (contoh: 300 detik = 5 menit)
refresh_interval = 300 

def main():
    st.title("✈️ Real-Time METAR & TAF - WIBB (Pekanbaru)")
    
    # Menampilkan indikator update otomatis
    st.caption(f"Aplikasi akan memperbarui data secara otomatis setiap {refresh_interval/60} menit.")

    # Ambil data langsung saat aplikasi dijalankan
    data = fetch_weather_data()
    
    if data:
        parts = data.strip().split('\n')
        
        # Layout Kolom
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📝 METAR (Observasi)")
            metar_text = next((s for s in parts if "METAR" in s), "Data METAR tidak ditemukan")
            st.info(metar_text)

        with col2:
            st.markdown("### 📅 TAF (Prakiraan)")
            taf_text = next((s for s in parts if "TAF" in s), "Data TAF tidak ditemukan")
            st.warning(taf_text)
            
        st.divider()
        st.write(f"✅ **Update Terakhir:** {datetime.now().strftime('%H:%M:%S')} WIB")

    # Perintah untuk refresh otomatis
    time.sleep(refresh_interval)
    st.rerun()

if __name__ == "__main__":
    main()