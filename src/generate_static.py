#!/usr/bin/env python3
"""
Professional Interactive Dashboard for Gulu Air Quality Monitor
Developed by CYPIS DataTelligence - Intelligent Systems for a Data-Driven Future
"""

import json
import os
from pathlib import Path
from datetime import datetime
import pytz

OUTPUT_DIR = '_site'
DATA_FILE = 'data/latest_readings.json'

# Uganda timezone (EAT - East Africa Time)
UGANDA_TZ = pytz.timezone('Africa/Kampala')

def get_uganda_time():
    """Get current time in Uganda (EAT)"""
    return datetime.now(UGANDA_TZ)

def format_uganda_time(dt=None):
    """Format datetime in Uganda timezone"""
    if dt is None:
        dt = get_uganda_time()
    elif isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            dt = dt.astimezone(UGANDA_TZ)
        except:
            dt = get_uganda_time()
    return dt.strftime('%d %b %Y, %H:%M:%S %Z')

def get_health_color_class(color):
    """Get CSS class for health color"""
    colors = {
        'green': 'bg-green-500',
        'yellow': 'bg-yellow-500',
        'orange': 'bg-orange-500',
        'red': 'bg-red-500',
        'purple': 'bg-purple-600',
        'maroon': 'bg-maroon-700',
        'gray': 'bg-gray-500'
    }
    return colors.get(color, 'bg-gray-500')

def get_health_advice(pm25):
    """Get health advice based on PM2.5 level"""
    if pm25 is None:
        return {
            'level': 'No Data',
            'color': 'gray',
            'advice': 'Data unavailable. Check back later.',
            'mask': 'N/A',
            'outdoor': 'N/A',
            'sensitive': 'N/A'
        }
    
    if pm25 <= 12:
        return {
            'level': 'Good',
            'color': 'green',
            'advice': 'Air quality is satisfactory. Enjoy outdoor activities safely.',
            'mask': 'Not required',
            'outdoor': 'Safe for all activities',
            'sensitive': 'No restrictions'
        }
    elif pm25 <= 35.4:
        return {
            'level': 'Moderate',
            'color': 'yellow',
            'advice': 'Acceptable quality. Sensitive individuals should limit prolonged outdoor exertion.',
            'mask': 'Optional for sensitive groups',
            'outdoor': 'Limited for sensitive groups',
            'sensitive': 'Consider reducing outdoor activities'
        }
    elif pm25 <= 55.4:
        return {
            'level': 'Unhealthy for Sensitive Groups',
            'color': 'orange',
            'advice': 'Members of sensitive groups may experience health effects. The general public is less likely to be affected.',
            'mask': 'Recommended for sensitive groups',
            'outdoor': 'Reduce for sensitive groups',
            'sensitive': 'Limit outdoor activities'
        }
    elif pm25 <= 150.4:
        return {
            'level': 'Unhealthy',
            'color': 'red',
            'advice': 'Everyone may begin to experience health effects. Sensitive groups may experience more serious effects.',
            'mask': 'Recommended for all',
            'outdoor': 'Limit for everyone',
            'sensitive': 'Avoid outdoor activities'
        }
    elif pm25 <= 250.4:
        return {
            'level': 'Very Unhealthy',
            'color': 'purple',
            'advice': 'Health alert: everyone may experience more serious health effects.',
            'mask': 'N95 recommended',
            'outdoor': 'Avoid',
            'sensitive': 'Stay indoors'
        }
    else:
        return {
            'level': 'Hazardous',
            'color': 'maroon',
            'advice': 'Health warnings of emergency conditions. Everyone is more likely to be affected.',
            'mask': 'N95 required',
            'outdoor': 'Stay indoors',
            'sensitive': 'Emergency protocols'
        }

def generate_station_cards(readings):
    """Generate HTML for station cards"""
    if not readings:
        return '<div class="col-span-3 text-center py-12 bg-white rounded-2xl shadow-md"><i class="fas fa-spinner fa-spin text-3xl text-gray-400 mb-3"></i><p class="text-gray-500">Waiting for data from Gulu monitoring stations...</p><p class="text-xs text-gray-400 mt-2">Data updates every hour</p></div>'
    
    cards = []
    for r in readings[:3]:
        pm25 = r.get('pm25', '--')
        pm10 = r.get('pm10', '--') or '--'
        category = r.get('category', 'Moderate')
        station = r.get('station_name', 'Gulu Station')
        aqi = r.get('aqi', '--')
        
        if aqi and isinstance(aqi, (int, float)):
            if aqi <= 50:
                badge_class = 'bg-green-500'
                gradient = 'from-green-50 to-emerald-50'
                ring = 'ring-green-500'
            elif aqi <= 100:
                badge_class = 'bg-yellow-500 text-gray-800'
                gradient = 'from-yellow-50 to-amber-50'
                ring = 'ring-yellow-500'
            elif aqi <= 150:
                badge_class = 'bg-orange-500'
                gradient = 'from-orange-50 to-amber-50'
                ring = 'ring-orange-500'
            elif aqi <= 200:
                badge_class = 'bg-red-500'
                gradient = 'from-red-50 to-rose-50'
                ring = 'ring-red-500'
            elif aqi <= 300:
                badge_class = 'bg-purple-600'
                gradient = 'from-purple-50 to-violet-50'
                ring = 'ring-purple-500'
            else:
                badge_class = 'bg-maroon-700'
                gradient = 'from-rose-50 to-red-50'
                ring = 'ring-red-600'
        else:
            badge_class = 'bg-gray-500'
            gradient = 'from-gray-50 to-slate-50'
            ring = 'ring-gray-400'
        
        if 'University' in station:
            station_icon = 'fa-university'
            station_color = 'text-emerald-600'
        elif 'Central' in station:
            station_icon = 'fa-chart-line'
            station_color = 'text-amber-600'
        else:
            station_icon = 'fa-microchip'
            station_color = 'text-blue-600'
        
        timestamp = r.get('timestamp', '')
        time_str = ''
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                dt = dt.astimezone(UGANDA_TZ)
                time_str = dt.strftime('%H:%M')
            except:
                pass
        
        cards.append(f'''
        <div class="bg-gradient-to-br {gradient} rounded-2xl shadow-lg overflow-hidden card">
            <div class="p-5">
                <div class="flex justify-between items-start">
                    <div>
                        <div class="flex items-center gap-2 mb-2">
                            <i class="fas {station_icon} {station_color} text-lg"></i>
                            <h3 class="font-bold text-gray-800">{station}</h3>
                        </div>
                        <p class="text-xs text-gray-500">Ground Monitoring Station</p>
                        {f'<p class="text-xs text-gray-400 mt-1"><i class="fas fa-clock mr-1"></i>{time_str}</p>' if time_str else ''}
                    </div>
                    <div class="relative">
                        <div class="w-14 h-14 rounded-full {badge_class} flex items-center justify-center text-white font-bold text-xl shadow-lg ring-2 {ring} ring-offset-2">
                            {aqi if aqi != '--' else '--'}
                        </div>
                        <div class="absolute -top-1 -right-1">
                            <div class="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                        </div>
                    </div>
                </div>
                <div class="mt-4 grid grid-cols-2 gap-3">
                    <div class="text-center p-3 bg-white/80 backdrop-blur rounded-xl shadow-sm">
                        <div class="text-2xl font-bold text-gray-800">{pm25}</div>
                        <div class="text-xs text-gray-500 flex items-center justify-center gap-1">
                            <i class="fas fa-smog"></i> PM2.5
                        </div>
                    </div>
                    <div class="text-center p-3 bg-white/80 backdrop-blur rounded-xl shadow-sm">
                        <div class="text-2xl font-bold text-gray-800">{pm10}</div>
                        <div class="text-xs text-gray-500 flex items-center justify-center gap-1">
                            <i class="fas fa-dust"></i> PM10
                        </div>
                    </div>
                </div>
                <div class="mt-3 text-center">
                    <span class="inline-block px-4 py-1.5 rounded-full text-xs font-semibold text-white {badge_class} shadow-sm">
                        <i class="fas fa-chart-line mr-1"></i> {category}
                    </span>
                </div>
            </div>
        </div>
        ''')
    
    return ''.join(cards)

def generate_table_rows(readings):
    """Generate HTML table rows"""
    if not readings:
        return '<tr><td colspan="6" class="text-center py-8 text-gray-500">No data yet. Check back soon.</td></tr>'
    
    rows = []
    for r in readings[:20]:
        timestamp = r.get('timestamp', '')
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            dt = dt.astimezone(UGANDA_TZ)
            formatted_time = dt.strftime('%d %b %H:%M')
            full_time = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            formatted_time = timestamp[:16] if timestamp else 'N/A'
            full_time = timestamp
        
        station = r.get('station_name', 'Gulu Station')
        pm25 = r.get('pm25', '--')
        pm10 = r.get('pm10', '--') or '--'
        aqi = r.get('aqi', '--')
        category = r.get('category', 'Moderate')
        
        if category == 'Good':
            badge_class = 'bg-green-100 text-green-700'
            icon = 'fa-smile'
        elif category == 'Moderate':
            badge_class = 'bg-yellow-100 text-yellow-700'
            icon = 'fa-meh'
        elif 'Unhealthy for Sensitive' in category:
            badge_class = 'bg-orange-100 text-orange-700'
            icon = 'fa-frown'
        elif 'Unhealthy' in category:
            badge_class = 'bg-red-100 text-red-700'
            icon = 'fa-frown-open'
        elif 'Very Unhealthy' in category:
            badge_class = 'bg-purple-100 text-purple-700'
            icon = 'fa-skull'
        else:
            badge_class = 'bg-gray-100 text-gray-700'
            icon = 'fa-exclamation-triangle'
        
        rows.append(f'''
        <tr class="border-t hover:bg-gray-50 transition">
            <td class="px-6 py-3 text-gray-600 text-sm" title="{full_time}">
                <i class="fas fa-clock text-gray-400 mr-1 text-xs"></i>
                {formatted_time}
            </td>
            <td class="px-6 py-3 font-medium text-gray-800">
                <i class="fas fa-location-dot text-gray-400 mr-1 text-xs"></i>
                {station}
            </td>
            <td class="px-6 py-3">{pm25}</td>
            <td class="px-6 py-3">{pm10}</td>
            <td class="px-6 py-3 font-semibold">{aqi}</td>
            <td class="px-6 py-3">
                <span class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs {badge_class}">
                    <i class="fas {icon} text-xs"></i>
                    {category}
                </span>
            </td>
        </tr>
        ''')
    
    return ''.join(rows)

def generate_html():
    """Generate the professional interactive dashboard"""
    
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Get current Uganda time
    current_time = get_uganda_time()
    current_time_str = format_uganda_time(current_time)
    
    # Load data
    latest_readings = []
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            latest_readings = data.get('readings', [])
    
    # Get latest reading for health advice
    latest_pm25 = latest_readings[0].get('pm25') if latest_readings else None
    health = get_health_advice(latest_pm25)
    
    # Get data retrieval timestamp
    data_retrieved_at = current_time_str
    if latest_readings and latest_readings[0].get('timestamp'):
        data_retrieved_at = format_uganda_time(latest_readings[0]['timestamp'])
    
    # Generate cards and table
    cards_html = generate_station_cards(latest_readings)
    table_html = generate_table_rows(latest_readings)
    
    # History data for chart
    history_data = [{'timestamp': r.get('timestamp', ''), 'pm25': r.get('pm25'), 'pm10': r.get('pm10')} for r in latest_readings[:48]]
    
    # Get health color class
    health_color_class = get_health_color_class(health['color'])
    
    # Generate HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gulu Air Quality Monitor | CYPIS DataTelligence</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{ font-family: 'Inter', system-ui, -apple-system, sans-serif; }}
        body {{ background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%); }}
        .gradient-header {{ background: linear-gradient(135deg, #0a2e1f 0%, #1a4d2e 100%); }}
        .card {{ transition: transform 0.3s ease, box-shadow 0.3s ease; }}
        .card:hover {{ transform: translateY(-5px); box-shadow: 0 20px 30px -15px rgba(0, 0, 0, 0.2); }}
        .stat-card {{ background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%); border: 1px solid rgba(0, 0, 0, 0.05); }}
        .refresh-btn {{ transition: all 0.3s ease; }}
        .refresh-btn:hover {{ transform: rotate(180deg); }}
        .cypis-badge {{ background: linear-gradient(135deg, #0B3B5F 0%, #1E6F5C 100%); }}
        .chart-container {{ position: relative; margin: auto; height: 300px; }}
        @media (max-width: 768px) {{ .chart-container {{ height: 250px; }} }}
        .bg-maroon-700 {{ background-color: #7e0023; }}
    </style>
</head>
<body>
    
    <div class="gradient-header text-white shadow-lg">
        <div class="max-w-7xl mx-auto px-4 py-5">
            <div class="flex flex-col md:flex-row justify-between items-center">
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 bg-white/10 backdrop-blur rounded-xl flex items-center justify-center">
                        <i class="fas fa-chart-line text-2xl text-green-300"></i>
                    </div>
                    <div>
                        <div class="flex items-center gap-2">
                            <h1 class="text-2xl md:text-3xl font-bold tracking-tight">Gulu Air Quality Monitor</h1>
                            <span class="bg-green-500/20 text-green-200 text-xs px-2 py-1 rounded-full animate-pulse">LIVE</span>
                        </div>
                        <p class="text-green-200 text-sm mt-1">Powered by CYPIS DataTelligence & Intelligent Systems</p>
                    </div>
                </div>
                <div class="mt-3 md:mt-0 text-right">
                    <div class="flex items-center gap-3">
                        <div class="text-right">
                            <div class="text-xs text-green-300">Data Source</div>
                            <div class="text-sm font-semibold">AirQo Network • Makerere University</div>
                        </div>
                        <div class="w-px h-10 bg-white/20"></div>
                        <div>
                            <i class="fas fa-map-marker-alt text-green-300"></i>
                            <span class="text-sm ml-1">Gulu City, Uganda</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="max-w-7xl mx-auto px-4 py-8">
        
        <!-- Timestamp Banner -->
        <div class="bg-gradient-to-r from-gray-800 to-gray-700 rounded-2xl shadow-lg mb-6 overflow-hidden">
            <div class="flex flex-wrap items-center justify-between px-6 py-4">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-cyan-500/20 rounded-full flex items-center justify-center">
                        <i class="fas fa-clock text-cyan-300 text-lg"></i>
                    </div>
                    <div>
                        <p class="text-xs text-gray-300 uppercase tracking-wider">DATA RETRIEVAL TIME</p>
                        <p class="text-lg md:text-xl font-mono font-bold text-white">{current_time_str}</p>
                    </div>
                </div>
                <div class="flex items-center gap-4">
                    <div class="text-right">
                        <p class="text-xs text-gray-300">Uganda Time (EAT)</p>
                        <p class="text-sm text-cyan-300" id="currentTime">{current_time_str}</p>
                    </div>
                    <button onclick="refreshData()" class="w-10 h-10 bg-white/10 rounded-full flex items-center justify-center hover:bg-white/20 transition refresh-btn">
                        <i class="fas fa-sync-alt text-white"></i>
                    </button>
                </div>
            </div>
            <div class="bg-black/20 px-6 py-2 text-xs text-gray-400 flex justify-between">
                <span><i class="fas fa-database mr-1"></i> Data from AirQo ground sensors</span>
                <span><i class="fas fa-chart-line mr-1"></i> Updated hourly</span>
                <span><i class="fas fa-map-marker-alt mr-1"></i> Gulu University • Kasubi Central • Layibi</span>
            </div>
        </div>
        
        <!-- Stats Overview -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div class="stat-card rounded-2xl p-4 shadow-md card">
                <div class="flex items-center justify-between">
                    <div><p class="text-gray-500 text-sm">Active Stations</p><p class="text-2xl font-bold text-gray-800">3</p></div>
                    <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center"><i class="fas fa-microphone-alt text-green-600"></i></div>
                </div>
                <p class="text-xs text-gray-400 mt-2">Gulu University • Kasubi • Layibi</p>
            </div>
            <div class="stat-card rounded-2xl p-4 shadow-md card">
                <div class="flex items-center justify-between">
                    <div><p class="text-gray-500 text-sm">Data Frequency</p><p class="text-2xl font-bold text-gray-800">Hourly</p></div>
                    <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center"><i class="fas fa-clock text-blue-600"></i></div>
                </div>
                <p class="text-xs text-gray-400 mt-2">Real-time updates</p>
            </div>
            <div class="stat-card rounded-2xl p-4 shadow-md card">
                <div class="flex items-center justify-between">
                    <div><p class="text-gray-500 text-sm">Coverage Area</p><p class="text-2xl font-bold text-gray-800">Northern Uganda</p></div>
                    <div class="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center"><i class="fas fa-globe-africa text-purple-600"></i></div>
                </div>
                <p class="text-xs text-gray-400 mt-2">Gulu Metropolitan Area</p>
            </div>
            <div class="stat-card rounded-2xl p-4 shadow-md card">
                <div class="flex items-center justify-between">
                    <div><p class="text-gray-500 text-sm">Last Reading</p><p class="text-lg font-bold text-gray-800">{data_retrieved_at.split(',')[1] if ',' in data_retrieved_at else data_retrieved_at}</p></div>
                    <div class="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center"><i class="fas fa-chart-simple text-amber-600"></i></div>
                </div>
                <p class="text-xs text-gray-400 mt-2">{data_retrieved_at.split(',')[0] if ',' in data_retrieved_at else 'Latest data'}</p>
            </div>
        </div>
        
        <!-- Station Cards -->
        <div class="grid lg:grid-cols-3 gap-6 mb-8">
            {cards_html}
        </div>
        
        <!-- Health Advisory -->
        <div class="grid lg:grid-cols-3 gap-6 mb-8">
            <div class="lg:col-span-2 bg-white rounded-2xl shadow-lg overflow-hidden card">
                <div class="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b">
                    <div class="flex items-center gap-2">
                        <i class="fas fa-heartbeat text-red-500 text-xl"></i>
                        <h3 class="font-bold text-gray-800">Health Advisory & Recommendations</h3>
                    </div>
                </div>
                <div class="p-6">
                    <div class="flex items-start gap-4">
                        <div class="w-16 h-16 rounded-full {health_color_class} flex items-center justify-center text-white font-bold text-xl shadow-lg">
                            {health['level'][0] if health['level'] else 'G'}
                        </div>
                        <div class="flex-1">
                            <h4 class="text-xl font-bold text-gray-800">{health['level']}</h4>
                            <p class="text-gray-600 mt-1">{health['advice']}</p>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mt-6 pt-4 border-t">
                        <div class="text-center p-2 rounded-lg hover:bg-gray-50 transition">
                            <i class="fas fa-mask text-gray-400 text-lg"></i>
                            <p class="text-xs text-gray-500 mt-1">Mask Recommendation</p>
                            <p class="text-sm font-semibold text-gray-700">{health['mask']}</p>
                        </div>
                        <div class="text-center p-2 rounded-lg hover:bg-gray-50 transition">
                            <i class="fas fa-tree text-gray-400 text-lg"></i>
                            <p class="text-xs text-gray-500 mt-1">Outdoor Activities</p>
                            <p class="text-sm font-semibold text-gray-700">{health['outdoor']}</p>
                        </div>
                        <div class="text-center p-2 rounded-lg hover:bg-gray-50 transition">
                            <i class="fas fa-users text-gray-400 text-lg"></i>
                            <p class="text-xs text-gray-500 mt-1">Sensitive Groups</p>
                            <p class="text-sm font-semibold text-gray-700">{health['sensitive']}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- AQI Guide -->
            <div class="bg-white rounded-2xl shadow-lg overflow-hidden card">
                <div class="bg-gradient-to-r from-gray-800 to-gray-700 px-6 py-4">
                    <div class="flex items-center gap-2">
                        <i class="fas fa-chart-simple text-white text-xl"></i>
                        <h3 class="font-bold text-white">Air Quality Index Guide</h3>
                    </div>
                </div>
                <div class="p-4">
                    <div class="space-y-2">
                        <div class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 transition cursor-pointer" onclick="showAQIInfo(0)">
                            <div class="flex items-center gap-3"><div class="w-4 h-4 rounded-full bg-green-500"></div><span class="text-sm font-medium">0-50</span><span class="text-sm text-gray-600">Good</span></div>
                            <i class="fas fa-info-circle text-gray-400 text-xs"></i>
                        </div>
                        <div class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 transition cursor-pointer" onclick="showAQIInfo(1)">
                            <div class="flex items-center gap-3"><div class="w-4 h-4 rounded-full bg-yellow-500"></div><span class="text-sm font-medium">51-100</span><span class="text-sm text-gray-600">Moderate</span></div>
                            <i class="fas fa-info-circle text-gray-400 text-xs"></i>
                        </div>
                        <div class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 transition cursor-pointer" onclick="showAQIInfo(2)">
                            <div class="flex items-center gap-3"><div class="w-4 h-4 rounded-full bg-orange-500"></div><span class="text-sm font-medium">101-150</span><span class="text-sm text-gray-600">Unhealthy for Sensitive</span></div>
                            <i class="fas fa-info-circle text-gray-400 text-xs"></i>
                        </div>
                        <div class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 transition cursor-pointer" onclick="showAQIInfo(3)">
                            <div class="flex items-center gap-3"><div class="w-4 h-4 rounded-full bg-red-500"></div><span class="text-sm font-medium">151-200</span><span class="text-sm text-gray-600">Unhealthy</span></div>
                            <i class="fas fa-info-circle text-gray-400 text-xs"></i>
                        </div>
                        <div class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 transition cursor-pointer" onclick="showAQIInfo(4)">
                            <div class="flex items-center gap-3"><div class="w-4 h-4 rounded-full bg-purple-600"></div><span class="text-sm font-medium">201-300</span><span class="text-sm text-gray-600">Very Unhealthy</span></div>
                            <i class="fas fa-info-circle text-gray-400 text-xs"></i>
                        </div>
                        <div class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 transition cursor-pointer" onclick="showAQIInfo(5)">
                            <div class="flex items-center gap-3"><div class="w-4 h-4 rounded-full" style="background-color: #7e0023;"></div><span class="text-sm font-medium">301+</span><span class="text-sm text-gray-600">Hazardous</span></div>
                            <i class="fas fa-info-circle text-gray-400 text-xs"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Chart Section -->
        <div class="bg-white rounded-2xl shadow-lg p-6 mb-8 card">
            <div class="flex flex-wrap justify-between items-center mb-6">
                <div><h3 class="font-bold text-xl text-gray-800">📊 Air Quality Trends</h3><p class="text-sm text-gray-500 mt-1">PM2.5 and PM10 concentration over time</p></div>
                <div class="flex gap-2">
                    <button onclick="setChartPeriod('24h')" class="px-3 py-1 text-sm rounded-lg bg-cyan-100 text-cyan-700 hover:bg-cyan-200 transition" id="btn24h">24 Hours</button>
                    <button onclick="setChartPeriod('7d')" class="px-3 py-1 text-sm rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 transition" id="btn7d">7 Days</button>
                </div>
            </div>
            <div class="chart-container"><canvas id="airQualityChart"></canvas></div>
            <div class="flex justify-center gap-6 mt-4">
                <div class="flex items-center gap-2"><div class="w-3 h-3 rounded-full bg-orange-500"></div><span class="text-xs text-gray-600">PM2.5 (µg/m³)</span></div>
                <div class="flex items-center gap-2"><div class="w-3 h-3 rounded-full bg-blue-500"></div><span class="text-xs text-gray-600">PM10 (µg/m³)</span></div>
                <div class="flex items-center gap-2"><div class="w-3 h-3 rounded-full bg-green-500"></div><span class="text-xs text-gray-600">WHO Guideline (15 µg/m³)</span></div>
            </div>
        </div>
        
        <!-- Recent Readings Table -->
        <div class="bg-white rounded-2xl shadow-lg overflow-hidden card">
            <div class="px-6 py-4 bg-gray-50 border-b flex flex-wrap justify-between items-center">
                <div class="flex items-center gap-2"><i class="fas fa-table text-gray-600"></i><h3 class="font-bold text-gray-800">Recent Readings</h3></div>
                <div class="relative"><i class="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-sm"></i><input type="text" id="searchInput" placeholder="Search station..." class="pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500"></div>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-sm" id="dataTable">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left cursor-pointer" onclick="sortTable(0)">Time <i class="fas fa-sort text-gray-400"></i></th>
                            <th class="px-6 py-3 text-left cursor-pointer" onclick="sortTable(1)">Station <i class="fas fa-sort text-gray-400"></i></th>
                            <th class="px-6 py-3 text-left cursor-pointer" onclick="sortTable(2)">PM2.5 <i class="fas fa-sort text-gray-400"></i></th>
                            <th class="px-6 py-3 text-left cursor-pointer" onclick="sortTable(3)">PM10 <i class="fas fa-sort text-gray-400"></i></th>
                            <th class="px-6 py-3 text-left cursor-pointer" onclick="sortTable(4)">AQI <i class="fas fa-sort text-gray-400"></i></th>
                            <th class="px-6 py-3 text-left">Status</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody">
                        {table_html}
                    </tbody>
                </table>
            </div>
            <div class="px-6 py-3 bg-gray-50 border-t text-xs text-gray-500 flex justify-between">
                <span>Showing <span id="rowCount">{len(latest_readings[:20])}</span> of {len(latest_readings)} readings</span>
                <span><i class="fas fa-clock mr-1"></i> Last data retrieved: {data_retrieved_at}</span>
            </div>
        </div>
        
        <!-- Footer -->
        <footer class="mt-8 pt-6 border-t border-gray-200">
            <div class="grid md:grid-cols-3 gap-6 text-sm">
                <div><div class="flex items-center gap-2 mb-3"><div class="w-8 h-8 cypis-badge rounded-lg flex items-center justify-center"><i class="fas fa-brain text-white text-sm"></i></div><span class="font-bold text-gray-800">CYPIS DataTelligence</span></div><p class="text-gray-500 text-xs">Intelligent Systems for a Data-Driven Future</p><p class="text-gray-400 text-xs mt-2">Gulu City, Uganda</p></div>
                <div><h4 class="font-semibold text-gray-700 mb-2">Contact</h4><p class="text-gray-500 text-xs"><i class="fas fa-phone-alt mr-2"></i>+256 780304392 (WhatsApp)</p><p class="text-gray-500 text-xs"><i class="fas fa-envelope mr-2"></i>iamonenjb@gmail.com</p><p class="text-gray-500 text-xs"><i class="fas fa-map-marker-alt mr-2"></i>Gulu City, Northern Uganda</p></div>
                <div><h4 class="font-semibold text-gray-700 mb-2">Data Partners</h4><p class="text-gray-500 text-xs">AirQo Network</p><p class="text-gray-500 text-xs">Makerere University</p><p class="text-gray-500 text-xs">Uganda National Environment Management Authority</p></div>
            </div>
            <div class="text-center mt-6 pt-4 border-t border-gray-200">
                <p class="text-xs text-gray-400">© 2025 CYPIS DataTelligence & Intelligent Systems. All rights reserved.</p>
                <p class="text-xs text-gray-400 mt-1">Real-time air quality monitoring for Gulu City | Data updated hourly | Last retrieved: {current_time_str}</p>
            </div>
        </footer>
    </div>
    
    <div id="aqiInfoPopup" class="hidden fixed inset-0 bg-black/50 flex items-center justify-center z-50" onclick="hideAQIInfo()">
        <div class="bg-white rounded-2xl p-6 max-w-sm mx-4" onclick="event.stopPropagation()">
            <h4 class="font-bold text-lg" id="aqiInfoTitle"></h4>
            <p class="text-gray-600 mt-2" id="aqiInfoText"></p>
            <button onclick="hideAQIInfo()" class="mt-4 bg-gray-800 text-white px-4 py-2 rounded-lg text-sm">Close</button>
        </div>
    </div>
    
    <script>
        let allReadings = {json.dumps([{
            'timestamp': r.get('timestamp', ''),
            'station_name': r.get('station_name', ''),
            'pm25': r.get('pm25', '--'),
            'pm10': r.get('pm10', '--'),
            'aqi': r.get('aqi', '--'),
            'category': r.get('category', '')
        } for r in latest_readings])};
        
        let chart = null;
        
        function updateCurrentTime() {{
            const now = new Date();
            const options = {{ year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: 'Africa/Kampala' }};
            document.getElementById('currentTime').textContent = now.toLocaleString('en-GB', options);
        }}
        setInterval(updateCurrentTime, 1000);
        
        function initChart() {{
            const historyData = {json.dumps(history_data)};
            const timestamps = historyData.map(d => {{
                const date = new Date(d.timestamp);
                return date.toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit' }});
            }});
            const pm25Values = historyData.map(d => d.pm25);
            const pm10Values = historyData.map(d => d.pm10 || 0);
            const ctx = document.getElementById('airQualityChart').getContext('2d');
            if (chart) chart.destroy();
            chart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: timestamps.reverse(),
                    datasets: [
                        {{ label: 'PM2.5 (µg/m³)', data: pm25Values.reverse(), borderColor: '#e86a3e', backgroundColor: 'rgba(232, 106, 62, 0.1)', fill: true, tension: 0.4, pointRadius: 3, pointBackgroundColor: '#e86a3e' }},
                        {{ label: 'PM10 (µg/m³)', data: pm10Values.reverse(), borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', fill: true, tension: 0.4, pointRadius: 3, pointBackgroundColor: '#3b82f6' }},
                        {{ label: 'WHO Guideline (15 µg/m³)', data: Array(timestamps.length).fill(15), borderColor: '#22c55e', borderDash: [5, 5], fill: false, pointRadius: 0, borderWidth: 2 }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{
                        legend: {{ position: 'top', labels: {{ usePointStyle: true, boxWidth: 8 }} }},
                        tooltip: {{ backgroundColor: 'rgba(0,0,0,0.8)' }}
                    }},
                    scales: {{
                        y: {{ beginAtZero: true, title: {{ display: true, text: 'Concentration (µg/m³)' }} }},
                        x: {{ title: {{ display: true, text: 'Time' }}, ticks: {{ maxRotation: 45, minRotation: 45 }} }}
                    }}
                }}
            }});
        }}
        
        function setChartPeriod(period) {{
            initChart();
        }}
        
        let sortColumn = 0, sortDirection = 'asc';
        function sortTable(column) {{
            if (sortColumn === column) sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            else {{ sortColumn = column; sortDirection = 'asc'; }}
            const sorted = [...allReadings].sort((a, b) => {{
                let aVal = Object.values(a)[column], bVal = Object.values(b)[column];
                if (column === 0) aVal = new Date(aVal), bVal = new Date(bVal);
                return sortDirection === 'asc' ? (aVal > bVal ? 1 : -1) : (aVal < bVal ? 1 : -1);
            }});
            renderTable(sorted);
        }}
        
        document.getElementById('searchInput')?.addEventListener('input', function(e) {{
            const term = e.target.value.toLowerCase();
            renderTable(allReadings.filter(r => r.station_name.toLowerCase().includes(term) || r.category.toLowerCase().includes(term)));
        }});
        
        function renderTable(data) {{
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = data.slice(0, 20).map(r => {{
                let badgeClass = '';
                let icon = '';
                if (r.category === 'Good') {{
                    badgeClass = 'bg-green-100 text-green-700';
                    icon = 'fa-smile';
                }} else if (r.category === 'Moderate') {{
                    badgeClass = 'bg-yellow-100 text-yellow-700';
                    icon = 'fa-meh';
                }} else if (r.category.includes('Unhealthy for Sensitive')) {{
                    badgeClass = 'bg-orange-100 text-orange-700';
                    icon = 'fa-frown';
                }} else if (r.category.includes('Unhealthy')) {{
                    badgeClass = 'bg-red-100 text-red-700';
                    icon = 'fa-frown-open';
                }} else if (r.category.includes('Very Unhealthy')) {{
                    badgeClass = 'bg-purple-100 text-purple-700';
                    icon = 'fa-skull';
                }} else {{
                    badgeClass = 'bg-gray-100 text-gray-700';
                    icon = 'fa-exclamation-triangle';
                }}
                return `<tr class="border-t hover:bg-gray-50">
                    <td class="px-6 py-3 text-sm">${{new Date(r.timestamp).toLocaleString()}}</td>
                    <td class="px-6 py-3 font-medium">${{r.station_name}}</td>
                    <td class="px-6 py-3">${{r.pm25}}</td>
                    <td class="px-6 py-3">${{r.pm10 || '--'}}</td>
                    <td class="px-6 py-3 font-semibold">${{r.aqi}}</td>
                    <td class="px-6 py-3"><span class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${badgeClass}"><i class="fas ${icon} text-xs"></i> ${{r.category}}</span></td>
                </tr>`;
            }}).join('') || '<tr><td colspan="6" class="text-center py-8 text-gray-500">No matching records found</td></tr>';
            document.getElementById('rowCount').textContent = data.length;
        }}
        
        function refreshData() {{ window.location.reload(); }}
        
        function showAQIInfo(idx) {{
            const info = [
                {{ title: 'Good (0-50)', text: 'Air quality is considered satisfactory, and air pollution poses little or no risk.' }},
                {{ title: 'Moderate (51-100)', text: 'Air quality is acceptable; however, for some pollutants there may be a moderate health concern for a very small number of people.' }},
                {{ title: 'Unhealthy for Sensitive Groups (101-150)', text: 'Members of sensitive groups may experience health effects. The general public is less likely to be affected.' }},
                {{ title: 'Unhealthy (151-200)', text: 'Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects.' }},
                {{ title: 'Very Unhealthy (201-300)', text: 'Health alert: everyone may experience more serious health effects.' }},
                {{ title: 'Hazardous (301+)', text: 'Health warnings of emergency conditions. The entire population is more likely to be affected.' }}
            ];
            document.getElementById('aqiInfoTitle').textContent = info[idx].title;
            document.getElementById('aqiInfoText').textContent = info[idx].text;
            document.getElementById('aqiInfoPopup').classList.remove('hidden');
        }}
        
        function hideAQIInfo() {{
            document.getElementById('aqiInfoPopup').classList.add('hidden');
        }}
        
        initChart();
        updateCurrentTime();
        renderTable(allReadings);
    </script>
</body>
</html>'''
    
    with open(f'{OUTPUT_DIR}/index.html', 'w') as f:
        f.write(html)
    
    print(f"✅ Professional dashboard generated at {OUTPUT_DIR}/index.html")
    print(f"   Data retrieved at: {current_time_str}")

if __name__ == '__main__':
    generate_html()
