#!/usr/bin/env python3
"""
Generate static HTML dashboard from REAL Gulu air quality data
"""

import json
import sqlite3
import os
from pathlib import Path
from datetime import datetime

DB_PATH = 'data/gulu_air_quality.db'
OUTPUT_DIR = '_site'
JSON_PATH = 'data/latest_readings.json'

def get_aqi_color(aqi: int) -> str:
    """Get color for AQI value"""
    if aqi is None:
        return '#888888'
    if aqi <= 50:
        return '#00e400'  # Good - Green
    elif aqi <= 100:
        return '#ffff00'  # Moderate - Yellow
    elif aqi <= 150:
        return '#ff7e00'  # Unhealthy for Sensitive - Orange
    elif aqi <= 200:
        return '#ff0000'  # Unhealthy - Red
    elif aqi <= 300:
        return '#8f3f97'  # Very Unhealthy - Purple
    else:
        return '#7e0023'  # Hazardous - Maroon

def generate_html():
    """Generate static HTML dashboard from real data"""
    
    # Check if data exists
    latest_data = []
    history_data = []
    
    if Path(JSON_PATH).exists():
        with open(JSON_PATH, 'r') as f:
            data = json.load(f)
            latest_data = data.get('latest', [])
            history_data = data.get('history', [])
    
    # Create output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Generate HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gulu City Air Quality Monitor | Real Data</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        * {{ font-family: 'Inter', sans-serif; }}
        .aqi-good {{ background: #00e400; color: #000; }}
        .aqi-moderate {{ background: #ffff00; color: #000; }}
        .aqi-unhealthy-sensitive {{ background: #ff7e00; color: #fff; }}
        .aqi-unhealthy {{ background: #ff0000; color: #fff; }}
        .aqi-very-unhealthy {{ background: #8f3f97; color: #fff; }}
        .aqi-hazardous {{ background: #7e0023; color: #fff; }}
        .last-updated {{
            font-size: 12px;
            color: #666;
            margin-top: 8px;
        }}
        .card {{
            transition: transform 0.2s;
        }}
        .card:hover {{
            transform: translateY(-4px);
        }}
    </style>
</head>
<body class="bg-gray-100">
    <div class="max-w-6xl mx-auto px-4 py-8">
        <!-- Header -->
        <div class="text-center mb-8">
            <div class="inline-flex items-center gap-2 bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm mb-3">
                <span>🟢 LIVE</span>
                <span>REAL DATA</span>
            </div>
            <h1 class="text-4xl md:text-5xl font-bold text-gray-800 mb-2">🌍 Gulu City Air Quality</h1>
            <p class="text-gray-600">Real-time data from AirQo ground monitoring stations</p>
            <p class="text-sm text-gray-500 mt-2">📍 Gulu University • Kasubi Central • Layibi</p>
            <div class="last-updated">
                Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                <br>Source: AirQo Network, Makerere University
            </div>
        </div>
        
        <!-- Current Conditions Cards -->
        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {''.join([f'''
            <div class="card bg-white rounded-2xl shadow-lg overflow-hidden">
                <div class="p-5">
                    <div class="flex justify-between items-start">
                        <div>
                            <h3 class="font-bold text-gray-800">{s.get('station_name', 'Gulu Station')}</h3>
                            <p class="text-xs text-gray-500 mt-1">Ground Sensor</p>
                        </div>
                        <div class="w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold {get_aqi_color(s.get('aqi', 50))}">
                            {s.get('aqi', '--')}
                        </div>
                    </div>
                    <div class="mt-4 grid grid-cols-2 gap-3">
                        <div class="text-center p-2 bg-gray-50 rounded-lg">
                            <div class="text-2xl font-bold text-gray-800">{s.get('pm25', '--')}</div>
                            <div class="text-xs text-gray-500">PM2.5 (µg/m³)</div>
                        </div>
                        <div class="text-center p-2 bg-gray-50 rounded-lg">
                            <div class="text-2xl font-bold text-gray-800">{s.get('pm10', '--') or '--'}</div>
                            <div class="text-xs text-gray-500">PM10 (µg/m³)</div>
                        </div>
                    </div>
                    <div class="mt-3 text-center">
                        <span class="inline-block px-3 py-1 rounded-full text-xs font-medium {get_aqi_color(s.get('aqi', 50))}">
                            {s.get('category', 'Unknown')}
                        </span>
                    </div>
                </div>
            </div>
            ''' for s in latest_data])}
        </div>
        
        <!-- Chart -->
        <div class="bg-white rounded-2xl shadow-lg p-6 mb-8">
            <h3 class="font-bold text-lg text-gray-800 mb-4">📊 PM2.5 Trend (Last 24 Hours)</h3>
            <canvas id="pm25Chart" height="200"></canvas>
            <p class="text-xs text-gray-500 text-center mt-4">Data from Gulu University monitoring station • Updated hourly</p>
        </div>
        
        <!-- Health Advisory -->
        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl shadow-lg p-6 mb-8">
            <h3 class="font-bold text-lg text-gray-800 mb-3">💡 Health Advisory</h3>
            <div id="health-advice" class="text-gray-700">
                Loading latest health recommendations...
            </div>
            <div class="mt-4 pt-3 border-t border-gray-200">
                <p class="text-xs text-gray-500">
                    ⚕️ Based on WHO Air Quality Guidelines • For sensitive groups: children, elderly, and those with respiratory conditions
                </p>
            </div>
        </div>
        
        <!-- About Section -->
        <div class="bg-white rounded-2xl shadow-lg p-6">
            <h3 class="font-bold text-lg text-gray-800 mb-3">📡 About This Data</h3>
            <div class="grid md:grid-cols-2 gap-6">
                <div>
                    <p class="text-gray-600 text-sm mb-2">
                        This dashboard displays <strong class="text-green-600">REAL air quality data</strong> from ground monitoring stations 
                        operated by <strong>AirQo</strong>, a project of Makerere University's College of Computing and Information Sciences.
                    </p>
                    <p class="text-gray-600 text-sm">
                        Gulu City currently has <strong>3 active monitoring stations</strong>:
                    </p>
                    <ul class="list-disc list-inside text-sm text-gray-600 mt-2">
                        <li>Gulu University Campus</li>
                        <li>Kasubi Central</li>
                        <li>Layibi</li>
                    </ul>
                </div>
                <div class="bg-gray-50 rounded-xl p-4">
                    <p class="text-sm font-semibold text-gray-700 mb-2">📋 Data Sources</p>
                    <p class="text-xs text-gray-500 mb-2">Primary: AirQo API (real-time ground sensors)</p>
                    <p class="text-xs text-gray-500">Update frequency: Hourly</p>
                    <p class="text-xs text-gray-500 mt-2">📍 Gulu, Northern Region, Uganda</p>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <footer class="text-center mt-8 pt-6 border-t border-gray-200">
            <p class="text-xs text-gray-500">
                Data provided by AirQo, Makerere University • System by CYPIS DataTelligence, Gulu
            </p>
            <p class="text-xs text-gray-400 mt-1">
                © 2025 • Real-time air quality monitoring for Gulu City
            </p>
        </footer>
    </div>
    
    <script>
        // Load history data for chart
        fetch('data.json')
            .then(response => response.json())
            .then(data => {{
                const history = data.history || [];
                const timestamps = history.map(d => new Date(d.timestamp).toLocaleTimeString());
                const pm25 = history.map(d => d.pm25);
                
                if (timestamps.length > 0 && pm25.length > 0) {{
                    const ctx = document.getElementById('pm25Chart').getContext('2d');
                    new Chart(ctx, {{
                        type: 'line',
                        data: {{
                            labels: timestamps.slice(-24).reverse(),
                            datasets: [{{
                                label: 'PM2.5 (µg/m³)',
                                data: pm25.slice(-24).reverse(),
                                borderColor: '#e86a3e',
                                backgroundColor: 'rgba(232, 106, 62, 0.1)',
                                fill: true,
                                tension: 0.3
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: true,
                            plugins: {{
                                legend: {{ position: 'top' }}
                            }}
                        }}
                    }});
                }}
                
                // Health advice based on latest reading
                const latest = data.latest?.[0];
                if (latest && latest.pm25) {{
                    let advice = '';
                    if (latest.pm25 <= 12) {{
                        advice = '✅ Air quality is GOOD. Enjoy outdoor activities safely.';
                    }} else if (latest.pm25 <= 35.4) {{
                        advice = '⚠️ Air quality is MODERATE. Sensitive individuals should limit prolonged outdoor exertion.';
                    }} else if (latest.pm25 <= 55.4) {{
                        advice = '⚠️ UNHEALTHY FOR SENSITIVE GROUPS. Children, elderly, and those with respiratory conditions should reduce outdoor activities.';
                    }} else if (latest.pm25 <= 150.4) {{
                        advice = '🚨 UNHEALTHY. Everyone may experience health effects. Limit outdoor activities. Wear a mask if going outside.';
                    }} else if (latest.pm25 <= 250.4) {{
                        advice = '🚨 VERY UNHEALTHY. Health alert. Avoid outdoor activities. Stay indoors with windows closed.';
                    }} else {{
                        advice = '🔥 HAZARDOUS! Health warning. Everyone is at risk. Stay indoors.';
                    }}
                    document.getElementById('health-advice').innerHTML = `
                        <p class="font-medium">Current PM2.5: ${latest.pm25} µg/m³ (${latest.category || 'Unknown'})</p>
                        <p class="mt-2">${advice}</p>
                    `;
                }}
            }})
            .catch(err => {{
                console.error('Error loading data:', err);
                document.getElementById('health-advice').innerHTML = '<p>Loading data from Gulu monitoring stations...</p>';
            }});
    </script>
</body>
</html>'''
    
    with open(f'{OUTPUT_DIR}/index.html', 'w') as f:
        f.write(html)
    
    print(f"✅ Dashboard generated at {OUTPUT_DIR}/index.html")


if __name__ == '__main__':
    generate_html()
