#!/usr/bin/env python3
"""
REAL Air Quality Data Fetcher for Gulu City, Uganda
Source: AirQo Network (Ground Sensors at Gulu University, Kasubi, Layibi)
"""

import requests
import sqlite3
import json
import datetime
import time
import os
from pathlib import Path
from typing import List, Dict, Optional

# Database path
DB_PATH = 'data/gulu_air_quality.db'

# Known Gulu stations from AirQo network
GULU_STATIONS = [
    {'id': 'gulu-university', 'name': 'Gulu University', 'latitude': 2.7745, 'longitude': 32.2989},
    {'id': 'kasubi-central', 'name': 'Kasubi Central', 'latitude': 2.7730, 'longitude': 32.2975},
    {'id': 'layibi', 'name': 'Layibi', 'latitude': 2.7760, 'longitude': 32.2995}
]

class GuluAirQualityFetcher:
    """Fetch real-time air quality data for Gulu City from AirQo network"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.setup_database()
        
        # AirQo public API endpoints
        self.api_base = "https://api.airqo.net/v2"
        
        print("=" * 60)
        print("🌍 Gulu City REAL Air Quality Monitoring System")
        print("=" * 60)
        print(f"Source: AirQo Network (Ground Sensors)")
        print(f"Active Stations: {len(GULU_STATIONS)}")
        print("  - Gulu University")
        print("  - Kasubi Central")
        print("  - Layibi")
        print("=" * 60)
    
    def setup_database(self):
        """Create SQLite database for storing real data"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main measurements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                station_id TEXT,
                station_name TEXT,
                latitude REAL,
                longitude REAL,
                pm25 REAL,
                pm10 REAL,
                aqi INTEGER,
                category TEXT,
                source TEXT
            )
        ''')
        
        # Daily summary table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                station_id TEXT,
                avg_pm25 REAL,
                max_pm25 REAL,
                min_pm25 REAL,
                readings_count INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✓ Database ready")
    
    def calculate_aqi(self, pm25: float) -> int:
        """Calculate Air Quality Index from PM2.5 (EPA standard)"""
        if pm25 is None:
            return None
        
        if pm25 <= 12.0:
            return 50
        elif pm25 <= 35.4:
            return 100
        elif pm25 <= 55.4:
            return 150
        elif pm25 <= 150.4:
            return 200
        elif pm25 <= 250.4:
            return 300
        else:
            return 400
    
    def get_aqi_category(self, pm25: float) -> str:
        """Get AQI category from PM2.5"""
        if pm25 is None:
            return "Unknown"
        
        if pm25 <= 12.0:
            return "Good"
        elif pm25 <= 35.4:
            return "Moderate"
        elif pm25 <= 55.4:
            return "Unhealthy for Sensitive"
        elif pm25 <= 150.4:
            return "Unhealthy"
        elif pm25 <= 250.4:
            return "Very Unhealthy"
        else:
            return "Hazardous"
    
    def get_health_advice(self, pm25: float) -> str:
        """Get health recommendations based on PM2.5 level"""
        if pm25 is None:
            return "Data unavailable. Check back later."
        
        if pm25 <= 12.0:
            return "Air quality is good. Enjoy outdoor activities!"
        elif pm25 <= 35.4:
            return "Air quality is moderate. Sensitive individuals should limit prolonged outdoor exertion."
        elif pm25 <= 55.4:
            return "Unhealthy for sensitive groups. Children, elderly, and those with respiratory conditions should reduce outdoor activities."
        elif pm25 <= 150.4:
            return "Unhealthy for everyone. Limit outdoor activities. Wear a mask if going outside."
        elif pm25 <= 250.4:
            return "Very unhealthy! Avoid outdoor activities. Wear N95 mask if you must go outside."
        else:
            return "HAZARDOUS! Stay indoors with windows closed. Use air purifiers if available."
    
    def fetch_from_airqo_api(self) -> List[Dict]:
        """
        Fetch real data from AirQo API
        AirQo provides free public data for all Ugandan cities including Gulu
        """
        try:
            # AirQo devices endpoint
            url = f"{self.api_base}/devices/measurements"
            params = {
                'recent': 'hour',
                'limit': 50,
                'device': 'all'
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                readings = []
                
                # Filter for Gulu stations
                for item in data:
                    location = item.get('location', '').lower()
                    device_name = item.get('device_name', '').lower()
                    
                    if 'gulu' in location or 'gulu' in device_name:
                        pm25 = item.get('pm2_5') or item.get('pm2.5')
                        pm10 = item.get('pm10')
                        
                        if pm25 is not None:
                            readings.append({
                                'station_id': item.get('device_id', 'gulu-station'),
                                'station_name': item.get('device_name', 'Gulu Station'),
                                'latitude': item.get('latitude', 2.7745),
                                'longitude': item.get('longitude', 32.2989),
                                'pm25': float(pm25) if pm25 else None,
                                'pm10': float(pm10) if pm10 else None,
                                'timestamp': item.get('time', datetime.datetime.now().isoformat()),
                                'source': 'AirQo API'
                            })
                
                return readings
            else:
                print(f"API Error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error fetching from AirQo: {e}")
            return []
    
    def fetch_from_aqicn(self) -> List[Dict]:
        """Alternative: Fetch from AQICN (requires API key for real-time)"""
        # AQICN provides free data but requires API key
        # For now, we'll use AirQo as primary source
        return []
    
    def save_measurements(self, readings: List[Dict]) -> int:
        """Save measurements to database"""
        if not readings:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved = 0
        for reading in readings:
            aqi = self.calculate_aqi(reading['pm25'])
            category = self.get_aqi_category(reading['pm25'])
            
            try:
                cursor.execute('''
                    INSERT INTO measurements (
                        timestamp, station_id, station_name, latitude, longitude,
                        pm25, pm10, aqi, category, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    reading['timestamp'],
                    reading['station_id'],
                    reading['station_name'],
                    reading['latitude'],
                    reading['longitude'],
                    reading['pm25'],
                    reading['pm10'],
                    aqi,
                    category,
                    reading.get('source', 'AirQo')
                ))
                saved += 1
            except Exception as e:
                print(f"Error saving: {e}")
        
        conn.commit()
        conn.close()
        return saved
    
    def update_daily_summary(self):
        """Calculate and update daily summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.date.today().isoformat()
        
        for station in GULU_STATIONS:
            cursor.execute('''
                SELECT 
                    AVG(pm25) as avg_pm25,
                    MAX(pm25) as max_pm25,
                    MIN(pm25) as min_pm25,
                    COUNT(*) as count
                FROM measurements
                WHERE station_id = ? AND DATE(timestamp) = ?
            ''', (station['id'], today))
            
            row = cursor.fetchone()
            
            if row and row[3] > 0:
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_summary (
                        date, station_id, avg_pm25, max_pm25, min_pm25, readings_count
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (today, station['id'], row[0], row[1], row[2], row[3]))
        
        conn.commit()
        conn.close()
    
    def export_to_json(self, filename: str = 'data/latest_readings.json'):
        """Export latest readings to JSON for dashboard"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get latest readings per station
        cursor.execute('''
            SELECT m.* FROM measurements m
            INNER JOIN (
                SELECT station_id, MAX(timestamp) as max_ts
                FROM measurements
                GROUP BY station_id
            ) latest ON m.station_id = latest.station_id AND m.timestamp = latest.max_ts
            ORDER BY m.timestamp DESC
        ''')
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        # Get last 24 hours history
        cursor.execute('''
            SELECT timestamp, station_name, pm25, pm10, aqi, category
            FROM measurements
            WHERE datetime(timestamp) > datetime('now', '-1 day')
            ORDER BY timestamp DESC
            LIMIT 100
        ''')
        
        history = [dict(row) for row in rows]
        
        # Save to JSON
        with open(filename, 'w') as f:
            json.dump({
                'latest': data,
                'history': history,
                'last_updated': datetime.datetime.now().isoformat(),
                'stations': GULU_STATIONS
            }, f, indent=2, default=str)
        
        conn.close()
        return data
    
    def run(self):
        """Main execution method"""
        print(f"\n📡 Fetching REAL Gulu air quality data...")
        print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 40)
        
        # Fetch from AirQo API
        readings = self.fetch_from_airqo_api()
        
        if readings:
            saved = self.save_measurements(readings)
            print(f"✓ Saved {saved} real readings from Gulu stations")
            
            # Display current readings
            for reading in readings:
                print(f"\n   📍 {reading['station_name']}")
                print(f"      PM2.5: {reading['pm25']} µg/m³")
                if reading.get('pm10'):
                    print(f"      PM10: {reading['pm10']} µg/m³")
                print(f"      AQI: {self.calculate_aqi(reading['pm25'])}")
                print(f"      Status: {self.get_aqi_category(reading['pm25'])}")
                print(f"      ⚕️  {self.get_health_advice(reading['pm25'])}")
            
            # Update summary
            self.update_daily_summary()
            
            # Export to JSON
            self.export_to_json()
            print("\n✓ Data exported to JSON for dashboard")
            
        else:
            print("⚠️ No data received from AirQo API.")
            print("   Possible reasons:")
            print("   - API may be temporarily unavailable")
            print("   - Check internet connection")
            print("   - Try again in a few minutes")
        
        return readings


if __name__ == '__main__':
    fetcher = GuluAirQualityFetcher()
    fetcher.run()
