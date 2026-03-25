#!/usr/bin/env python3
"""
Gulu Air Quality Dashboard Generator - Shows ALL Stations
"""

import json
import os
from pathlib import Path
from datetime import datetime
import pytz

OUTPUT_DIR = '_site'
DATA_FILE = 'data/latest_readings.json'
UGANDA_TZ = pytz.timezone('Africa/Kampala')

def format_time(dt=None):
    if dt is None:
        dt = datetime.now(UGANDA_TZ)
    return dt.strftime('%d %b %Y, %H:%M:%S')

def generate_html():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Load data
    latest_readings = []
    data_source = "No Data"
    
    if Path(DATA_FILE).exists():
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                latest_readings = data.get('readings', [])
                data_source = data.get('source', 'No Data')
                print(f"✅ Loaded {len(latest_readings)} readings from JSON")
        except Exception as e:
            print(f"⚠️ Error loading JSON: {e}")
    else:
        print(f"⚠️ JSON file not found: {DATA_FILE}")
    
    current_time = format_time()
    
    # Get the LATEST reading for each station (by timestamp)
    latest_by_station = {}
    for r in latest_readings:
        station = r.get('station_name', '')
        timestamp = r.get('timestamp', '')
        if station and (station not in latest_by_station or timestamp > latest_by_station[station]['timestamp']):
            latest_by_station[station] = r
    
    print(f"📊 Found {len(latest_by_station)} unique stations: {list(latest_by_station.keys())}")
    
    # Generate station cards for ALL stations
    cards_html = ''
    if latest_by_station:
        for station_name, r in latest_by_station.items():
            pm25 = r.get('pm25', '--')
            pm10 = r.get('pm10', '--') or '--'
            category = r.get('category', 'Moderate')
            aqi = r.get('aqi', '--')
            
            # Set color based on AQI category
            if category == 'Good':
                color = 'bg-green-500'
            elif category == 'Moderate':
                color = 'bg-yellow-500'
            elif 'Unhealthy' in category:
                color = 'bg-red-500'
            elif 'Hazardous' in category:
                color = 'bg-purple-600'
            else:
                color = 'bg-gray-500'
            
            cards_html += f'''
            <div class="bg-white rounded-xl shadow-lg p-5 card-hover">
                <div class="flex justify-between items-start">
                    <div>
                        <h3 class="font-bold text-lg text-gray-800">{station_name}</h3>
                        <p class="text-xs text-gray-500">Ground Monitoring Station</p>
                    </div>
                    <div class="w-12 h-12 rounded-full {color} flex items-center justify-center text-white font-bold text-lg">
                        {aqi}
                    </div>
                </div>
                <div class="mt-4 grid grid-cols-2 gap-3">
                    <div class="text-center p-2 bg-gray-50 rounded-lg">
                        <div class="text-2xl font-bold text-gray-800">{pm25}</div>
                        <div class="text-xs text-gray-500">PM2.5 (µg/m³)</div>
                    </div>
                    <div class="text-center p-2 bg-gray-50 rounded-lg">
                        <div class="text-2xl font-bold text-gray-800">{pm10}</div>
                        <div class="text-xs text-gray-500">PM10 (µg/m³)</div>
                    </div>
                </div>
                <div class="mt-3 text-center">
                    <span class="inline-block px-3 py-1 rounded-full text-xs text-white {color}">
                        {category}
                    </span>
                </div>
            </div>
            '''
    else:
        cards_html = '''
        <div class="col-span-3 text-center py-12 bg-white rounded-xl shadow-md">
            <i class="fas fa-spinner fa-spin text-3xl text-gray-400 mb-3"></i>
            <p class="text-gray-500">Waiting for data from Gulu monitoring stations...</p>
            <p class="text-xs text-gray-400 mt-2">Data updates every hour from AQICN</p>
        </div>
        '''
    
    # Generate table rows for ALL readings
    table_html = ''
    if latest_readings:
        for r in latest_readings[:30]:
            timestamp = r.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                dt = dt.astimezone(UGANDA_TZ)
                formatted_time = dt.strftime('%d %b %H:%M')
            except:
                formatted_time = timestamp[:16] if timestamp else 'N/A'
            
            station = r.get('station_name', '')
            pm25 = r.get('pm25', '--')
            pm10 = r.get('pm10', '--') or '--'
            aqi = r.get('aqi', '--')
            category = r.get('category', '')
            
            if category == 'Good':
                badge = 'bg-green-100 text-green-700'
                icon = 'fa-smile'
            elif category == 'Moderate':
                badge = 'bg-yellow-100 text-yellow-700'
                icon = 'fa-meh'
            elif 'Unhealthy' in category:
                badge = 'bg-red-100 text-red-700'
                icon = 'fa-frown'
            else:
                badge = 'bg-gray-100 text-gray-700'
                icon = 'fa-chart-line'
            
            table_html += f'''
            <tr class="border-t hover:bg-gray-50">
                <td class="px-4 py-3 text-gray-600">{formatted_time}</td>
                <td class="px-4 py-3 font-medium text-gray-800">{station}</td>
                <td class="px-4 py-3">{pm25}</td>
                <td class="px-4 py-3">{pm10}</td>
                <td class="px-4 py-3 font-semibold">{aqi}</td>
                <td class="px-4 py-3">
                    <span class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs {badge}">
                        <i class="fas {icon} text-xs"></i> {category}
                    </span>
                </td>
            </tr>
            '''
    else:
        table_html = '<tr><td colspan="6" class="text-center py-8 text-gray-500">No data yet. Check back soon.</td></tr>'
    
    # Health advice based on highest AQI (most severe)
    health_advice = "Loading air quality data from Gulu monitoring stations..."
    if latest_readings:
        # Find highest AQI (most severe)
        highest_aqi = max((r.get('aqi', 0) for r in latest_readings if r.get('aqi')), default=None)
        if highest_aqi:
            if highest_aqi <= 50:
                health_advice = "✅ Air quality is GOOD. Enjoy outdoor activities safely."
            elif highest_aqi <= 100:
                health_advice = "⚠️ Air quality is MODERATE. Sensitive individuals should limit prolonged outdoor exertion."
            elif highest_aqi <= 150:
                health_advice = "⚠️ UNHEALTHY FOR SENSITIVE GROUPS. Children and elderly should reduce outdoor activities."
            elif highest_aqi <= 200:
                health_advice = "🚨 UNHEALTHY. Everyone may experience health effects. Limit outdoor activities."
            elif highest_aqi <= 300:
                health_advice = "🚨 VERY UNHEALTHY. Health alert. Avoid outdoor activities."
            else:
                health_advice = "🔥 HAZARDOUS! Stay indoors with windows closed."
    
    # Generate full HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gulu Air Quality Monitor | CYPIS DataTelligence</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{ font-family: 'Inter', system-ui, sans-serif; }}
        body {{ background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%); }}
        .card-hover {{ transition: transform 0.2s ease, box-shadow 0.2s ease; }}
        .card-hover:hover {{ transform: translateY(-4px); box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1); }}
        .gradient-header {{ background: linear-gradient(135deg, #0a2e1f 0%, #1a4d2e 100%); }}
        .cypis-badge {{ background: linear-gradient(135deg, #0B3B5F 0%, #1E6F5C 100%); }}
    </style>
</head>
<body>
    <div class="gradient-header text-white shadow-lg">
        <div class="max-w-6xl mx-auto px-4 py-6">
            <div class="flex flex-col md:flex-row justify-between items-center">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center">
                        <i class="fas fa-chart-line text-xl text-green-300"></i>
                    </div>
                    <div>
                        <h1 class="text-2xl md:text-3xl font-bold">🌍 Gulu Air Quality Monitor</h1>
                        <p class="text-green-200 text-sm">Powered by CYPIS DataTelligence | University of the Sacred Heart Gulu</p>
                    </div>
                </div>
                <div class="mt-3 md:mt-0 text-right">
                    <div class="text-sm text-green-200">Data Source: AQICN (Real-time)</div>
                    <div class="text-xs text-green-300">Updated: {current_time}</div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="max-w-6xl mx-auto px-4 py-8">
        
        <!-- Stats Banner -->
        <div class="bg-gradient-to-r from-gray-800 to-gray-700 rounded-2xl shadow-lg mb-6">
            <div class="flex flex-wrap items-center justify-between px-6 py-4">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-cyan-500/20 rounded-full flex items-center justify-center">
                        <i class="fas fa-chart-simple text-cyan-300"></i>
                    </div>
                    <div>
                        <p class="text-xs text-gray-300">ACTIVE MONITORING STATIONS</p>
                        <p class="text-2xl font-bold text-white">{len(latest_by_station)} Stations</p>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <i class="fas fa-map-marker-alt text-gray-400"></i>
                    <span class="text-sm text-gray-300">Gulu City, Uganda</span>
                </div>
            </div>
        </div>
        
        <!-- Station Cards - All Stations -->
        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {cards_html}
        </div>
        
        <!-- Health Advisory -->
        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl shadow-md p-6 mb-8">
            <div class="flex items-start gap-4">
                <div class="text-3xl">💡</div>
                <div>
                    <h3 class="font-bold text-lg text-gray-800">Health Advisory</h3>
                    <p class="text-gray-700 mt-1">{health_advice}</p>
                    <p class="text-xs text-gray-500 mt-3">Based on WHO Air Quality Guidelines • Sensitive groups: children, elderly, respiratory conditions</p>
                </div>
            </div>
        </div>
        
        <!-- Recent Readings Table -->
        <div class="bg-white rounded-xl shadow-lg overflow-hidden">
            <div class="px-6 py-4 bg-gray-50 border-b">
                <h3 class="font-bold text-gray-800">📋 Recent Readings</h3>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-4 py-3 text-left">Time</th>
                            <th class="px-4 py-3 text-left">Station</th>
                            <th class="px-4 py-3 text-left">PM2.5</th>
                            <th class="px-4 py-3 text-left">PM10</th>
                            <th class="px-4 py-3 text-left">AQI</th>
                            <th class="px-4 py-3 text-left">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_html}
                    </tbody>
                </table>
            </div>
            <div class="px-6 py-3 bg-gray-50 border-t text-xs text-gray-500 flex justify-between">
                <span>Showing {min(len(latest_readings), 30)} of {len(latest_readings)} readings</span>
                <span>Data source: {data_source}</span>
            </div>
        </div>
        
        <!-- Footer -->
        <footer class="mt-8 pt-6 border-t border-gray-200 text-center text-sm text-gray-500">
            <p>Air quality data provided by <strong>AQICN / World Air Quality Index Project</strong></p>
            <p class="mt-1">System by <strong>CYPIS DataTelligence</strong> | University of the Sacred Heart Gulu</p>
            <p class="mt-1">Contact: <a href="https://wa.me/256779753870" class="text-green-600">+256 779753870 (WhatsApp)</a></p>
        </footer>
    </div>
</body>
</html>'''
    
    # Save to both locations
    with open(f'{OUTPUT_DIR}/index.html', 'w') as f:
        f.write(html)
    with open('index.html', 'w') as f:
        f.write(html)
    
    print(f"✅ Dashboard generated at {OUTPUT_DIR}/index.html")
    print(f"   Stations displayed: {len(latest_by_station)}")
    print(f"   Total readings: {len(latest_readings)}")

if __name__ == '__main__':
    generate_html()
