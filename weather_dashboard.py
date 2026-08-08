#!/usr/bin/env python3
"""
Weather Dashboard
=================
A beautiful Streamlit weather dashboard built with `requests` + OpenWeatherMap API.

Features:
  - Live weather (current conditions)
  - 7-day forecast
  - Air quality index (AQI)
  - Interactive maps (folium)

Author: DAA Project
License: MIT
"""

import os
import time
import datetime as dt
import requests
import streamlit as st

# ============================================================================
# Constants
# ============================================================================

# OpenWeatherMap API base URL
GEO_URL = "http://api.openweathermap.org/geo/1.0/direct"
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"
AIR_URL = "http://api.openweathermap.org/data/2.5/air_pollution"

# Weather condition -> emoji + color mapping
WEATHER_ICONS = {
    "clear": "☀️", "clouds": "☁️", "rain": "🌧️", "drizzle": "🌦️",
    "thunderstorm": "⛈️", "snow": "❄️", "mist": "🌫️", "fog": "🌫️",
    "haze": "🌥️", "smoke": "💨", "dust": "🌪️", "sand": "🌪️",
    "ash": "🌋", "squall": "🌬️", "tornado": "🌪️",
}

# AQI scale (US EPA): aqi -> (label, color, health)
AQI_LEVELS = [
    (50, "Good", "#4CAF50", "Air quality is satisfactory, little or no risk."),
    (100, "Moderate", "#FFC107", "Acceptable. Sensitive people may experience minor effects."),
    (150, "Unhealthy for Sensitive Groups", "#FF9800", "Sensitive groups may experience health effects."),
    (200, "Unhealthy", "#F44336", "Everyone may begin to experience health effects."),
    (300, "Very Unhealthy", "#9C27B0", "Health alert: everyone may experience serious effects."),
    (500, "Hazardous", "#7B1FA2", "Emergency conditions: serious health effects."),
]

DEFAULT_CITY = "Bengaluru"
GOOGLE_MAPS_TILE = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"


# ============================================================================
# API Helpers
# ============================================================================

def get_api_key():
    """Resolve API key from env or sidebar."""
    key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not key:
        key = st.session_state.get("api_key", "").strip()
    return key


def geocode(city, api_key):
    """Get lat/lon for a city using OpenWeatherMap geocoding API."""
    params = {"q": city, "limit": 1, "appid": api_key}
    resp = requests.get(GEO_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return None, None, None
    return data[0]["lat"], data[0]["lon"], data[0]["name"]


def fetch_current_weather(lat, lon, api_key, units="metric"):
    """Fetch current weather for coordinates."""
    params = {"lat": lat, "lon": lon, "appid": api_key, "units": units}
    resp = requests.get(WEATHER_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_forecast(lat, lon, api_key, units="metric"):
    """Fetch 5-day/3-hour forecast and aggregate into 7 daily buckets."""
    params = {"lat": lat, "lon": lon, "appid": api_key, "units": units}
    resp = requests.get(FORECAST_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # Group by day
    daily = {}
    for item in data.get("list", []):
        dt_obj = dt.datetime.fromtimestamp(item["dt"])
        day_key = dt_obj.strftime("%A")
        if day_key not in daily:
            daily[day_key] = {
                "temps": [], "descs": [], "icons": [],
                "humidity": [], "wind": [], "pops": [],
            }
        d = daily[day_key]
        d["temps"].append(item["main"]["temp"])
        d["descs"].append(item["weather"][0]["description"])
        d["icons"].append(item["weather"][0]["main"])
        d["humidity"].append(item["main"]["humidity"])
        d["wind"].append(item["wind"]["speed"])
        d["pops"].append(item.get("pop", 0))

    # Build forecast list (limit to 7 days)
    forecast = []
    for day_key, d in list(daily.items())[:7]:
        forecast.append({
            "day": day_key,
            "min": round(min(d["temps"])),
            "max": round(max(d["temps"])),
            "desc": max(set(d["descs"]), key=d["descs"].count),
            "icon": max(set(d["icons"]), key=d["icons"].count),
            "humidity": round(sum(d["humidity"]) / len(d["humidity"])),
            "wind": round(sum(d["wind"]) / len(d["wind"]), 1),
            "pop": round(max(d["pops"]) * 100),
        })
    return forecast


def fetch_air_quality(lat, lon, api_key):
    """Fetch air pollution data."""
    params = {"lat": lat, "lon": lon, "appid": api_key}
    resp = requests.get(AIR_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data["list"][0]


def aqi_info(aqi):
    """Return (label, color, health) for the given AQI value."""
    for max_val, label, color, health in AQI_LEVELS:
        if aqi <= max_val:
            return label, color, health
    label, color, health = AQI_LEVELS[-1]
    return label, color, health


def pollutant_label(key):
    """Human-friendly label for pollutant keys."""
    labels = {
        "co": "CO", "no": "NO", "no2": "NO₂", "o3": "O₃",
        "so2": "SO₂", "pm2_5": "PM2.5", "pm10": "PM10", "nh3": "NH₃",
    }
    return labels.get(key, key.upper())


# ============================================================================
# UI / CSS
# ============================================================================

def load_css():
    """Inject custom CSS for a polished, modern look with rich HTML."""
    st.markdown("""
    <style>
    /* Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: radial-gradient(circle at 15% 15%, #1e3c72 0%, #0f2027 45%, #2c5364 100%);
        background-attachment: fixed;
    }
    /* Animated floating blobs */
    .blob {
        position: fixed;
        border-radius: 50%;
        filter: blur(80px);
        opacity: 0.35;
        z-index: 0;
        pointer-events: none;
    }
    /* Hide Streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 1.5rem; position: relative; z-index: 1;}

    /* Hero title */
    .hero {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        color: #7fd4ff;
        border-radius: 30px;
        padding: 0.3rem 1.2rem;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 0.8rem;
    }
    .hero h1 {
        font-size: 3.2rem;
        font-weight: 900;
        background: linear-gradient(90deg, #00c6ff, #0072ff, #00e5ff, #00c6ff);
        background-size: 300% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 4s linear infinite;
        margin: 0;
    }
    @keyframes shine {
        to { background-position: 300% center; }
    }
    .hero p {
        color: #a9c1d4;
        font-size: 1.1rem;
        margin-top: 0.4rem;
    }

    /* Current weather card */
    .weather-card {
        background: linear-gradient(135deg, rgba(30,60,114,0.9) 0%, rgba(42,82,152,0.9) 100%);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 24px;
        padding: 2rem 2.2rem;
        color: white;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        margin-bottom: 1rem;
        position: relative;
        overflow: hidden;
    }
    .weather-card::before {
        content: "";
        position: absolute;
        top: -60px; right: -60px;
        width: 220px; height: 220px;
        background: radial-gradient(circle, rgba(255,255,255,0.15), transparent 70%);
        border-radius: 50%;
    }
    .weather-main {
        display: flex;
        align-items: center;
        gap: 2rem;
        position: relative;
        z-index: 1;
    }
    .weather-icon {
        font-size: 6rem;
        filter: drop-shadow(0 8px 16px rgba(0,0,0,0.4));
        animation: float 3s ease-in-out infinite;
    }
    @keyframes float {
        0%,100% { transform: translateY(0); }
        50% { transform: translateY(-8px); }
    }
    .weather-temp {
        font-size: 5rem;
        font-weight: 900;
        line-height: 1;
        text-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .weather-desc {
        font-size: 1.5rem;
        font-weight: 700;
        text-transform: capitalize;
    }
    .weather-loc {
        font-size: 1rem;
        opacity: 0.9;
        margin-top: 0.3rem;
    }
    .weather-meta {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 0.9rem;
        margin-top: 1.5rem;
        position: relative;
        z-index: 1;
    }
    .meta-item {
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(6px);
        border-radius: 16px;
        padding: 0.9rem 0.6rem;
        text-align: center;
        transition: transform 0.2s, background 0.2s;
    }
    .meta-item:hover { background: rgba(255,255,255,0.18); transform: translateY(-3px); }
    .meta-item .label { font-size: 0.75rem; opacity: 0.85; }
    .meta-item .value { font-size: 1.25rem; font-weight: 800; margin-top: 0.2rem; }

    /* Section titles */
    .section-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #e0f2fe;
        margin: 2rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .section-title::after {
        content: "";
        flex: 1;
        height: 2px;
        background: linear-gradient(90deg, rgba(127,212,255,0.4), transparent);
        margin-left: 0.5rem;
    }

    /* Forecast card */
    .forecast-card {
        background: linear-gradient(160deg, rgba(30,60,114,0.75) 0%, rgba(15,32,39,0.9) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 18px;
        padding: 1.1rem 0.6rem;
        text-align: center;
        color: white;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        height: 100%;
        transition: transform 0.25s, box-shadow 0.25s;
    }
    .forecast-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 16px 40px rgba(0,0,0,0.6);
        border-color: rgba(127,212,255,0.4);
    }
    .fc-day { font-weight: 700; font-size: 0.95rem; color: #7fd4ff; }
    .fc-icon { font-size: 2.6rem; margin: 0.4rem 0; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3)); }
    .fc-temp { font-size: 1.3rem; font-weight: 900; }
    .fc-desc { font-size: 0.75rem; opacity: 0.85; text-transform: capitalize; min-height: 1rem; }
    .fc-extra { font-size: 0.7rem; color: #90caf9; margin-top: 0.4rem; }
    .fc-bar {
        height: 5px;
        border-radius: 5px;
        background: linear-gradient(90deg, #00c6ff, #ff9800);
        margin: 0.5rem auto 0 auto;
        width: 80%;
    }

    /* AQI card with gauge */
    .aqi-card {
        background: linear-gradient(135deg, rgba(20,30,48,0.9) 0%, rgba(36,59,85,0.9) 100%);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 24px;
        padding: 2rem;
        color: white;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        text-align: center;
        margin-bottom: 1rem;
    }
    .aqi-gauge {
        width: 160px;
        height: 160px;
        border-radius: 50%;
        margin: 0 auto 1rem auto;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 40px rgba(0,0,0,0.5), inset 0 0 20px rgba(255,255,255,0.1);
    }
    .aqi-value { font-size: 3.5rem; font-weight: 900; line-height: 1; }
    .aqi-unit { font-size: 0.75rem; opacity: 0.8; margin-top: 0.2rem; }
    .aqi-label { font-size: 1.3rem; font-weight: 800; margin-top: 0.5rem; }
    .aqi-health { font-size: 0.85rem; opacity: 0.85; margin-top: 0.5rem; padding: 0 1rem; }

    /* Pollutant card */
    .pollutant-card {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1rem 0.6rem;
        text-align: center;
        transition: transform 0.2s, background 0.2s;
    }
    .pollutant-card:hover { background: rgba(255,255,255,0.14); transform: translateY(-3px); }
    .poll-value { font-size: 1.6rem; font-weight: 900; color: #7fd4ff; }
    .poll-label { font-size: 0.75rem; color: #a9c1d4; font-weight: 600; }

    /* Map wrapper */
    .map-wrap {
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 24px;
        overflow: hidden;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    }

    /* Time refresh */
    .refresh-note {
        text-align: center;
        color: #7f9db2;
        font-size: 0.85rem;
        margin-top: 2rem;
        padding-bottom: 1rem;
    }

    /* Sidebar polish */
    .css-1d391kg, .stSidebar { background: #0b151c; }
    .stSidebar { border-right: 1px solid rgba(255,255,255,0.06); }
    </style>
    """, unsafe_allow_html=True)


def render_current_weather(data, city):
    """Render the current weather hero card."""
    icon_main = data["weather"][0]["main"].lower()
    emoji = WEATHER_ICONS.get(icon_main, "🌤️")
    temp = round(data["main"]["temp"])
    feels = round(data["main"]["feels_like"])
    desc = data["weather"][0]["description"].capitalize()
    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    wind = data["wind"]["speed"]
    visibility = data.get("visibility", 0) / 1000
    sunrise = dt.datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%I:%M %p")
    sunset = dt.datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%I:%M %p")
    country = data["sys"].get("country", "")

    st.markdown(f"""
    <div class="weather-card">
        <div class="weather-main">
            <div class="weather-icon">{emoji}</div>
            <div>
                <div class="weather-temp">{temp}°C</div>
                <div class="weather-desc">{desc}</div>
                <div class="weather-loc">📍 {city}, {country} · Feels like {feels}°C</div>
            </div>
        </div>
        <div class="weather-meta">
            <div class="meta-item"><div class="label">💧 Humidity</div><div class="value">{humidity}%</div></div>
            <div class="meta-item"><div class="label">🌬️ Wind</div><div class="value">{wind} m/s</div></div>
            <div class="meta-item"><div class="label">🌡️ Pressure</div><div class="value">{pressure} hPa</div></div>
            <div class="meta-item"><div class="label">👁️ Visibility</div><div class="value">{visibility:.1f} km</div></div>
            <div class="meta-item"><div class="label">🌅 Sunrise</div><div class="value">{sunrise}</div></div>
            <div class="meta-item"><div class="label">🌇 Sunset</div><div class="value">{sunset}</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_forecast(forecast):
    """Render 7-day forecast cards."""
    cols = st.columns(7)
    for col, day in zip(cols, forecast):
        icon_main = day["icon"].lower()
        emoji = WEATHER_ICONS.get(icon_main, "🌤️")
        span = max(30, min(100, (day["max"] - day["min"]) * 6))
        col.markdown(f"""
        <div class="forecast-card">
            <div class="fc-day">{day['day']}</div>
            <div class="fc-icon">{emoji}</div>
            <div class="fc-temp">{day['max']}° / {day['min']}°</div>
            <div class="fc-desc">{day['desc']}</div>
            <div class="fc-bar" style="width:{span}%"></div>
            <div class="fc-extra">💧 {day['humidity']}% · 🌬️ {day['wind']} · ☔ {day['pop']}%</div>
        </div>
        """, unsafe_allow_html=True)


def render_air_quality(data):
    """Render AQI gauge and pollutant levels."""
    aqi = data["main"]["aqi"]
    comp = data["components"]
    label, color, health = aqi_info(aqi)

    st.markdown(f"""
    <div class="aqi-card">
        <div class="aqi-gauge" style="background:conic-gradient({color} 0% {aqi/5:.0f}%, rgba(255,255,255,0.08) {aqi/5:.0f}% 100%);">
            <div class="aqi-value" style="color:{color}">{aqi}</div>
            <div class="aqi-unit">US AQI</div>
        </div>
        <div class="aqi-label" style="color:{color}">{label}</div>
        <div class="aqi-health">{health}</div>
    </div>
    """, unsafe_allow_html=True)

    # Pollutant cards
    st.markdown('<div class="section-title">🧪 Pollutant Levels (µg/m³)</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    for i, (key, value) in enumerate(comp.items()):
        cols[i % 4].markdown(f"""
        <div class="pollutant-card">
            <div class="poll-value">{value:.1f}</div>
            <div class="poll-label">{pollutant_label(key)}</div>
        </div>
        """, unsafe_allow_html=True)


def render_map(lat, lon, city):
    """Render an interactive folium map."""
    import folium
    from streamlit_folium import folium_static

    m = folium.Map(
        location=[lat, lon],
        zoom_start=10,
        tiles="OpenStreetMap",
        width="100%",
        height=420,
    )

    # Add a marker with a popup
    folium.Marker(
        [lat, lon],
        popup=f"<b>{city}</b><br>Lat: {lat:.4f}<br>Lon: {lon:.4f}",
        tooltip=city,
        icon=folium.Icon(color="red", icon="cloud", prefix="fa"),
    ).add_to(m)

    # Add a circle around the location for visual appeal
    folium.Circle(
        location=[lat, lon],
        radius=5000,
        color="#00c6ff",
        fill=True,
        fill_color="#00c6ff",
        fill_opacity=0.15,
    ).add_to(m)

    folium_static(m, width="100%", height=420)


# ============================================================================
# Main App
# ============================================================================

def main():
    st.set_page_config(
        page_title="Weather Dashboard",
        page_icon="🌦️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    load_css()

    # Sidebar
    st.sidebar.title("🌦️ Weather Dashboard")
    st.sidebar.markdown("---")

    api_key = get_api_key()
    if not api_key:
        api_key = st.sidebar.text_input(
            "🔑 OpenWeatherMap API Key",
            type="password",
            help="Get a free key at openweathermap.org",
            key="api_key",
        )

    st.sidebar.markdown("### 🔍 Search")
    city = st.sidebar.text_input("City", value=DEFAULT_CITY)
    search_btn = st.sidebar.button("Get Weather", type="primary", use_container_width=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "**💡 Tip:** Get a free API key at "
        "[openweathermap.org](https://openweathermap.org/api) to unlock live data."
    )

# Background blobs
    st.markdown("""
    <div class="blob" style="top:-80px; left:-80px; width:300px; height:300px; background:#0072ff;"></div>
    <div class="blob" style="bottom:-100px; right:-60px; width:350px; height:350px; background:#00e5ff;"></div>
    <div class="blob" style="top:40%; right:20%; width:200px; height:200px; background:#7c4dff;"></div>
    """, unsafe_allow_html=True)

    # Hero
    st.markdown("""
    <div class="hero">
        <div class="hero-badge">⚡ Live Weather · 7-Day Forecast · Air Quality · Maps</div>
        <h1>🌦️ Weather Dashboard</h1>
        <p>Real-time weather insights, beautifully rendered</p>
    </div>
    """, unsafe_allow_html=True)

    if not api_key:
        st.info("👈 Please enter your OpenWeatherMap API key in the sidebar to get started.")
        return

    if not search_btn and getattr(st.session_state, "has_data", False):
        return

    # Fetch data
    try:
        with st.spinner(f"Fetching weather for {city}..."):
            lat, lon, resolved_name = geocode(city, api_key)
            if lat is None:
                st.error(f"❌ City '{city}' not found. Please check the spelling.")
                return

            weather = fetch_current_weather(lat, lon, api_key)
            forecast = fetch_forecast(lat, lon, api_key)
            air = fetch_air_quality(lat, lon, api_key)

            dt_obj = dt.datetime.fromtimestamp(weather["dt"])
            st.session_state.has_data = True
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            st.error("❌ Invalid API key. Please check your OpenWeatherMap API key.")
        else:
            st.error(f"❌ API error: {e}")
        return
    except Exception as e:
        st.error(f"❌ Something went wrong: {e}")
        return

    # Current weather
    st.markdown(f'<div class="section-title">🌡️ Current Weather</div>', unsafe_allow_html=True)
    render_current_weather(weather, resolved_name)

    # 7-day forecast
    st.markdown('<div class="section-title">📅 7-Day Forecast</div>', unsafe_allow_html=True)
    render_forecast(forecast)

    # Air quality + Map side by side
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.markdown('<div class="section-title">🌬️ Air Quality</div>', unsafe_allow_html=True)
        render_air_quality(air)
    with col2:
        st.markdown('<div class="section-title">🗺️ Map</div>', unsafe_allow_html=True)
        render_map(lat, lon, resolved_name)

    st.markdown(
        f'<div class="refresh-note">🔄 Last updated: {dt_obj.strftime("%A, %B %d, %Y · %I:%M %p")} · '
        f'Data by OpenWeatherMap</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
