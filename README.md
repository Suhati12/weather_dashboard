# 🌦️ Weather Dashboard

A beautiful, feature-rich weather dashboard built with **Streamlit** and **requests**, powered by the **OpenWeatherMap API**. Inspired by the popular [re4day weather dashboard](https://github.com/re4day/Weather-Dashboards).

# ✨ Features

| Feature | Description |
|---------|-------------|
| 🌡️ **Live Weather** | Current temperature, feels-like, humidity, wind, pressure, visibility, sunrise/sunset |
| 📅 **7-Day Forecast** | Daily high/low temps, condition, humidity, wind & rain chance |
| 🌬️ **Air Quality** | Real-time AQI with US EPA scale + pollutant levels (PM2.5, PM10, O3, NO2, SO2, CO, NH3) |
| 🗺️ **Interactive Map** | Folium map with city marker and surrounding area highlight |

## 🚀 How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run weather_dashboard.py
```

## 🔑 Get an API Key

1. Create a free account at [OpenWeatherMap](https://openweathermap.org/api)
2. Generate an API key from your dashboard
3. Enter the key in the app's sidebar (or set it as the `OPENWEATHER_API_KEY` environment variable)

## 📖 Usage

1. Enter your **API key** in the sidebar
2. Type a **city name** (e.g., "Bengaluru")
3. Click **"Get Weather"**
4. View live weather, 7-day forecast, air quality, and the interactive map

## 📁 Project Structure

```
weather_dashboard/
├── weather_dashboard.py   # Main Streamlit app
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## 🛠️ Tech Stack

- **Streamlit** — web UI framework
- **requests** — HTTP client for the OpenWeatherMap API
- **folium** + **streamlit-folium** — interactive maps
- **OpenWeatherMap API** — live weather, forecast & air-quality data

## 📝 Notes

- The free OpenWeatherMap forecast tier provides 5-day/3-hour data, which is aggregated into 7 daily summaries.
- Air Quality Index uses the US EPA standard.

## 📜 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Inspired by [re4day/Weather-Dashboards](https://github.com/re4day/Weather-Dashboards)
- Data provided by the [OpenWeatherMap API](https://openweathermap.org/api)
