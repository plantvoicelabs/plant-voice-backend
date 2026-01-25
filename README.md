# 🌱 Plant Voice Labs - IoT Backend

**Making plants "talk" using IoT + AI.**

Plant Voice Labs is an open-source platform that translates plant sensor data into natural language, helping anyone understand what their plants need - from home gardeners to farmers to researchers.

## 🎯 Mission

Empowering everyone with affordable, AI-powered plant monitoring technology. No expensive equipment, no complex dashboards - just your plant telling you what it needs in simple language.

## 🚀 Tech Stack

- **FastAPI** - Python web framework
- **InfluxDB** - Time-series database
- **Claude AI** - Natural language generation
- **Railway** - Cloud deployment

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/sensors/data | Receive sensor data from ESP32 |
| GET | /api/v1/sensors/health | Health check |
| GET | /api/v1/ai/interpret | Get AI interpretation of sensor data |
| POST | /api/v1/speech/generate | Generate TTS audio from text |
| GET | /api/v1/dashboard/status | Get dashboard status |
| GET | /api/v1/dashboard/sensors | Get current sensor readings |
| GET | /api/v1/dashboard/latest-message | Get latest AI message with audio |
| GET | /api/v1/dashboard/history | Get 24-hour sensor history |
| POST | /api/v1/dashboard/trigger-message | Manually trigger AI message |

## 🌡️ Sensors Supported

- Temperature & Humidity (DHT22)
- Light Intensity (BH1750)
- Soil Moisture (Capacitive)
- TDS - Total Dissolved Solids
- pH Level

## 🤖 Features

- **AI Interpretation**: Generates natural language responses based on sensor data and peer-reviewed agricultural research
- **Voice Synthesis**: Converts AI messages to speech using ElevenLabs API
- **Smart Scheduler**: Follows plant rhythms with morning greetings (6 AM), periodic reports (8 AM - 8 PM), goodnight messages (10 PM), and sleep mode overnight
- **Real-time Dashboard API**: Provides endpoints for live sensor data, AI messages, and historical charts

## 🛠️ Development Status

| Component | Status |
|-----------|--------|
| IoT Gateway | ✅ Done |
| InfluxDB Integration | ✅ Done |
| AI Engine | ✅ Done |
| Text-to-Speech | ✅ Done |
| Smart Scheduler | ✅ Done |
| Dashboard API | ✅ Done |

## 🌍 Why Open Source?

We believe smart plant care should be accessible to everyone. By making Plant Voice Labs open source, we hope to:

- Help anyone monitor their plants affordably
- Enable communities to adapt the system for local needs
- Build a global community of contributors

## 📦 Installation

1. Clone this repository
2. Create virtual environment
3. Install dependencies with `pip install -r requirements.txt`
4. Create `.env` file with your credentials
5. Run with `uvicorn app.main:app --reload`

## ⚙️ Environment Variables

Create a `.env` file with:

- INFLUXDB_URL
- INFLUXDB_TOKEN
- INFLUXDB_ORG
- INFLUXDB_BUCKET
- API_SECRET_KEY
- ALLOWED_DEVICE_IDS
- OPENROUTER_API_KEY
- ELEVENLABS_API_KEY

## 🤝 Contributing

We welcome contributions! Whether you're a developer, hobbyist, farmer, or researcher - your input matters.

- Found a bug? Open an issue
- Have an idea? Start a discussion
- Want to code? Submit a pull request

## 📄 License

MIT - Free to use, modify, and distribute.

## 🔗 Links

- Website: [plantvoicelabs.com](https://plantvoicelabs.com)
- Twitter: [@plantvoicelabs](https://x.com/plantvoicelabs)

---