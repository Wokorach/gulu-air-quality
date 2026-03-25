#!/usr/bin/env python3
"""
Gulu Air Quality Dashboard Generator - Saves to root and _site
"""

import json
import os
from pathlib import Path
from datetime import datetime
import pytz

OUTPUT_DIR = '_site'
DATA_FILE = 'data/latest_readings.json'

UGANDA_TZ = pytz.timezone('Africa/Kampala')

def get_uganda_time():
    return datetime.now(UGANDA_TZ)

def format_time(dt=None):
    if dt is None:
        dt = get_uganda_time()
    return dt.strftime('%d %b %Y, %H:%M:%S')

def generate_html():
    # Create directories
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Load data
    latest_readings = []
    data_source = "Unknown"
    
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            latest_readings = data.get('readings', [])
            data_source = data.get('source', 'AirQo API')
    
    current_time = format_time()
    
    # Get data retrieval timestamp
    data_retrieved_at = current_time
    if latest_readings and latest_readings[0].get('timestamp'):
        try:
            dt = datetime.fromisoformat(latest_readings[0]['timestamp'].replace('Z', '+00:00'))
            dt = dt.astimezone(UGANDA_TZ)
            data_retrieved_at = dt.strftime('%d %b %Y, %H:%M:%S')
        except:
            pass
    
    # Generate station cards
    cards_html = ''
    if latest_readings:
        # Group by station to show latest per station
        stations_seen = set()
        station_readings = []
        for r in latest_readings:
            station = r.get('station_name', '')
            if station not in stations_seen:
                stations_seen.add(station)
                station_readings.append(r)
        
        for r in station_readings[:3]:
            pm25 = r.get('pm25', '--')
            pm10 = r.get('pm10', '--') or '--'
            category = r.get('category', 'Moderate')
            station = r.get('station_name', 'Gulu Station')
            aqi = r.get('aqi', '--')
            
            # Set color based on category
            if category == 'Good':
                color = 'bg-green-500'
            elif category == 'Moderate':
                color = 'bg-yellow-500'
            elif 'Unhealthy' in category:
                color = 'bg-red-500'
            else:
                color = 'bg-gray-500'
            
            cards_html += f'''
            <div class="bg-white rounded-xl shadow-lg p-5 card-hover">
                <div class="flex justify-between items-start">
                    <div>
                        <h3 class="font-bold text-lg text-gray-800">{station}</h3>
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
            <p class="text-gray-500">Loading data from Gulu monitoring stations...</p>
            <p class="text-xs text-gray-400 mt-2">Data updates every hour</p>
        </div>
        '''
    
    # Generate table rows
    table_html = ''
    if latest_readings:
        for r in latest_readings[:20]:
            timestamp = r.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                dt = dt.astimezone(UGANDA_TZ)
                formatted_time = dt.strftime('%d %b %H:%M')
            except:
                formatted_time = timestamp[:16] if timestamp else 'N/A'
            
            station = r.get('station_name', 'Gulu Station')
            pm25 = r.get('pm25', '--')
            pm10 = r.get('pm10', '--') or '--'
            aqi = r.get('aqi', '--')
            category = r.get('category', 'Moderate')
            
            # Set badge style
            if category == 'Good':
                badge_style = 'bg-green-100 text-green-700'
                icon = 'fa-smile'
            elif category == 'Moderate':
                badge_style = 'bg-yellow-100 text-yellow-700'
                icon = 'fa-meh'
            elif 'Unhealthy' in category:
                badge_style = 'bg-red-100 text-red-700'
                icon = 'fa-frown'
            else:
                badge_style = 'bg-gray-100 text-gray-700'
                icon = 'fa-chart-line'
            
            table_html += f'''
            <tr class="border-t hover:bg-gray-50">
                <td class="px-4 py-3 text-gray-600">{formatted_time}</td>
                <td class="px-4 py-3 font-medium text-gray-800">{station}</td>
                <td class="px-4 py-3">{pm25}</td>
                <td class="px-4 py-3">{pm10}</td>
                <td class="px-4 py-3 font-semibold">{aqi}</td>
                <td class="px-4 py-3">
                    <span class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs {badge_style}">
                        <i class="fas {icon} text-xs"></i> {category}
                    </span>
                </td>
            </tr>
            '''
    else:
        table_html = '<tr><td colspan="6" class="text-center py-8 text-gray-500">No data yet. Check back soon.</td></tr>'
    
    # Generate health advice based on latest reading
    health_advice = "Loading air quality data from Gulu monitoring stations..."
    if latest_readings and latest_readings[0].get('pm25'):
        pm25_val = latest_readings[0]['pm25']
        if pm25_val <= 12:
            health_advice = "✅ Air quality is GOOD. Enjoy outdoor activities safely."
        elif pm25_val <= 35.4:
            health_advice = "⚠️ Air quality is MODERATE. Sensitive individuals should limit prolonged outdoor exertion."
        elif pm25_val <= 55.4:
            health_advice = "⚠️ UNHEALTHY FOR SENSITIVE GROUPS. Children and elderly should reduce outdoor activities."
        elif pm25_val <= 150.4:
            health_advice = "🚨 UNHEALTHY. Everyone may experience health effects. Limit outdoor activities."
        elif pm25_val <= 250.4:
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
    
    <!-- Header -->
    <div class="gradient-header text-white shadow-lg">
        <div class="max-w-6xl mx-auto px-4 py-6">
            <div class="flex flex-col md:flex-row justify-between items-center">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center">
                        <i class="fas fa-chart-line text-xl text-green-300"></i>
                    </div>
                    <div>
                        <h1 class="text-2xl md:text-3xl font-bold">🌍 Gulu Air Quality Monitor</h1>
                        <p class="text-green-200 text-sm">Powered by CYPIS DataTelligence</p>
                    </div>
                </div>
                <div class="mt-3 md:mt-0 text-right">
                    <div class="text-sm text-green-200">AirQo Network • Makerere University</div>
                    <div class="text-xs text-green-300 mt-1">Gulu City, Uganda</div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="max-w-6xl mx-auto px-4 py-8">
        
        <!-- Timestamp Banner -->
        <div class="bg-gradient-to-r from-gray-800 to-gray-700 rounded-2xl shadow-lg mb-6">
            <div class="flex flex-wrap items-center justify-between px-6 py-4">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-cyan-500/20 rounded-full flex items-center justify-center">
                        <i class="fas fa-clock text-cyan-300"></i>
                    </div>
                    <div>
                        <p class="text-xs text-gray-300">DATA RETRIEVAL TIME</p>
                        <p class="text-lg font-mono font-bold text-white">{current_time}</p>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <i class="fas fa-map-marker-alt text-gray-400"></i>
                    <span class="text-sm text-gray-300">Gulu University • Kasubi • Layibi</span>
                </div>
            </div>
        </div>
        
        <!-- Stats Overview -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div class="bg-white rounded-xl shadow-md p-4 card-hover">
                <div class="flex justify-between items-center">
                    <div><p class="text-gray-500 text-sm">Active Stations</p><p class="text-2xl font-bold">3</p></div>
                    <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center"><i class="fas fa-microphone-alt text-green-600"></i></div>
                </div>
                <p class="text-xs text-gray-400 mt-2">Gulu University • Kasubi • Layibi</p>
            </div>
            <div class="bg-white rounded-xl shadow-md p-4 card-hover">
                <div class="flex justify-between items-center">
                    <div><p class="text-gray-500 text-sm">Data Frequency</p><p class="text-2xl font-bold">Hourly</p></div>
                    <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center"><i class="fas fa-clock text-blue-600"></i></div>
                </div>
                <p class="text-xs text-gray-400 mt-2">Real-time updates</p>
            </div>
            <div class="bg-white rounded-xl shadow-md p-4 card-hover">
                <div class="flex justify-between items-center">
                    <div><p class="text-gray-500 text-sm">Coverage Area</p><p class="text-2xl font-bold">Northern Uganda</p></div>
                    <div class="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center"><i class="fas fa-globe-africa text-purple-600"></i></div>
                </div>
                <p class="text-xs text-gray-400 mt-2">Gulu Metropolitan Area</p>
            </div>
            <div class="bg-white rounded-xl shadow-md p-4 card-hover">
                <div class="flex justify-between items-center">
                    <div><p class="text-gray-500 text-sm">Last Reading</p><p class="text-sm font-bold text-gray-800">{data_retrieved_at}</p></div>
                    <div class="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center"><i class="fas fa-chart-simple text-amber-600"></i></div>
                </div>
            </div>
        </div>
        
        <!-- Station Cards -->
        <div class="grid md:grid-cols-3 gap-6 mb-8">
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
                <span>Showing {len(latest_readings[:20])} of {len(latest_readings)} readings</span>
                <span><i class="fas fa-clock mr-1"></i> Data source: {data_source}</span>
            </div>
        </div>
        
        <!-- Footer with WhatsApp Contact -->
        <footer class="mt-8 pt-6 border-t border-gray-200">
            <div class="grid md:grid-cols-3 gap-6 text-sm">
                <div>
                    <div class="flex items-center gap-2 mb-3">
                        <div class="w-8 h-8 cypis-badge rounded-lg flex items-center justify-center">
                            <i class="fas fa-brain text-white text-sm"></i>
                        </div>
                        <span class="font-bold text-gray-800">CYPIS DataTelligence</span>
                    </div>
                    <p class="text-gray-500 text-xs">Intelligent Systems for a Data-Driven Future</p>
                    <p class="text-gray-400 text-xs mt-2">Gulu City, Uganda</p>
                </div>
                <div>
                    <h4 class="font-semibold text-gray-700 mb-2">Contact</h4>
                    <p class="text-gray-500 text-xs">
                        <i class="fab fa-whatsapp text-green-600 mr-2"></i>
                        <a href="https://wa.me/256779753870" target="_blank" class="hover:text-green-600">+256 779753870 (WhatsApp)</a>
                    </p>
                </div>
                <div>
                    <h4 class="font-semibold text-gray-700 mb-2">Data Partners</h4>
                    <p class="text-gray-500 text-xs">AirQo Network • Makerere University</p>
                    <p class="text-gray-500 text-xs">Uganda National Environment Management Authority</p>
                </div>
            </div>
            <div class="text-center mt-6 pt-4 border-t border-gray-200">
                <p class="text-xs text-gray-400">© 2025 CYPIS DataTelligence & Intelligent Systems. All rights reserved.</p>
                <p class="text-xs text-gray-400 mt-1">Real-time air quality monitoring for Gulu City | Data updated hourly</p>
            </div>
        </footer>
    </div>
</body>
</html>'''
    
    # Save to BOTH locations
    # 1. Save to _site for GitHub Pages artifact
    with open(f'{OUTPUT_DIR}/index.html', 'w') as f:
        f.write(html)
    
    # 2. Save to root for direct access
    with open('index.html', 'w') as f:
        f.write(html)
    
    print(f"✅ Dashboard saved to:")
    print(f"   - {OUTPUT_DIR}/index.html")
    print(f"   - index.html (root)")
    print(f"   Readings: {len(latest_readings)}")

if __name__ == '__main__':
    generate_html()
