THRESHOLD_GENERATION_PROMPT = """\
You are a plant care expert. Generate sensor thresholds for the plant type specified below.

Plant: {plant_name}

Respond with ONLY valid JSON in this exact format, no explanation, no markdown:
{{"temperature": {{"min": 0, "max": 0}}, "humidity": {{"min": 0, "max": 0}}, "pressure": {{"min": 0, "max": 0}}, "light": {{"min": 0, "max": 0}}, "soil_moisture": {{"min": 0, "max": 0}}}}

Units: temperature in °C, humidity in %, pressure in hPa, light as relative index (0-1000), soil_moisture in %.
Reference light levels (relative index 0-1000):
- Aloe Vera: 200–800 (bright indirect light)
- Tomato: 400–900 (high light)
- Spider Plant: 100–600 (low-medium light)
- Default for most plants: 100–700
"""

ANOMALY_EXPLANATION_PROMPT = """\
You are a plant health assistant. Explain the following sensor anomalies for a plant. Do NOT decide whether they are anomalies — that has already been determined. Only explain what these conditions mean for the plant and suggest corrective actions.

Plant: {plant_name}

Current sensor readings:
- Temperature: {temperature}°C
- Humidity: {humidity}%
- Pressure: {pressure} hPa
- Light: {light} lux* (relative index 0-1000)
- Soil Moisture: {soil_moisture}%

Anomalies detected:
{anomaly_list}

Last 3 readings for trend context:
{trend_context}

Write a concise, plain-English explanation (3-5 sentences) of what these conditions mean for the plant and what the grower should do. No bullet points, no headers.
"""
