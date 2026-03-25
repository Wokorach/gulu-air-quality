#!/usr/bin/env python3
"""
Real Gulu Air Quality Data Fetcher - With Sample Data Fallback
"""

import requests
import json
import sqlite3
import os
from pathlib import Path
from datetime import datetime, timedelta
import pytz

DB_PATH = 'data/gulu_air_quality.db'
UGANDA_TZ = pytz.timezone('Africa/Kampala')

class GuluAirQuality:
    def __init__(self):
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        self.setup_db()
        print("=" * 50)
        print("🌍 Gulu Air Quality Data Fetcher")
        print("=" * 50)
    
    def setup_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                station_name TEXT,
                pm25 REAL,
                pm10 REAL,
                aqi INTEGER,
                category TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def get_category(self, pm25):
        if pm25 <= 12:
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
    
    def get_aqi(self, pm25):
        if pm25 <= 12:
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
    
    def create_sample_data(self):
        """Create realistic sample data for Gulu City"""
        now = datetime.now(UGANDA_TZ)
        sample_readings = []
        
        # Gulu stations with realistic coordinates
        stations = [
            {'name': 'Gulu University', 'base_pm25': 28, 'base_pm10': 45},
            {'name': 'Kasubi Central', 'base_pm25': 32, 'base_pm10': 52},
            {'name': 'Layibi', 'base_pm25': 25, 'base_pm10': 40}
        ]
        
        for station in stations:
            # Generate 24 hours of data (last 24 hours)
            for i in range(24):
                hour = now - timedelta(hours=i)
                # Add some variation based on time of day
                hour_of_day = hour.hour
                if 7 <= hour_of_day <= 9:  # Morning rush
                    factor = 1.5
                elif 17 <= hour_of_day <= 19:  # Evening rush
                    factor = 1.4
                elif 22 <= hour_of_day or hour_of_day <= 5:  # Night
                    factor = 0.7
                else:
                    factor = 1.0
                
                # Add random variation
                import random
                random_factor = random.uniform(0.8, 1.2)
                
                pm25 = round(station['base_pm25'] * factor * random_factor, 1)
                pm10 = round(station['base_pm10'] * factor * random_factor, 1)
                
                # Ensure values are reasonable
                pm25 = min(max(pm25, 5), 150)
                pm10 = min(max(pm10, 10), 200)
                
                sample_readings.append({
                    'station': station['name'],
                    'pm25': pm25,
                    'pm10': pm10,
                    'timestamp': hour.isoformat()
                })
        
        # Sort by timestamp (newest first)
        sample_readings.sort(key=lambda x: x['timestamp'], reverse=True)
        return sample_readings
    
    def fetch_from_airqo(self):
        """Try to fetch real data from AirQo API"""
        try:
            url = "https://api.airqo.net/v2/devices/measurements"
            params = {'recent': 'hour', 'limit': 50}
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"⚠️ API returned status {response.status_code}")
                return []
            
            data = response.json()
            readings = []
            
            # Look for Gulu in the data
            for item in data:
                location = item.get('location', '').lower()
                device_name = item.get('device_name', '').lower()
                
                if 'gulu' in location or 'gulu' in device_name:
                    pm25 = item.get('pm2_5') or item.get('pm2.5')
                    if pm25:
                        readings.append({
                            'station': item.get('device_name', 'Gulu Station'),
                            'pm25': float(pm25),
                            'pm10': float(item.get('pm10', 0)) if item.get('pm10') else None,
                            'timestamp': item.get('time', datetime.now().isoformat())
                        })
            
            if readings:
                print(f"✅ Found {len(readings)} real readings from Gulu")
            else:
                print("⚠️ No Gulu data found in API response")
            
            return readings
        except Exception as e:
            print(f"⚠️ API Error: {e}")
            return []
    
    def save_readings(self, readings):
        """Save readings to database"""
        if not readings:
            return 0
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        saved = 0
        for r in readings:
            aqi = self.get_aqi(r['pm25'])
            category = self.get_category(r['pm25'])
            try:
                cursor.execute('''
                    INSERT INTO measurements (timestamp, station_name, pm25, pm10, aqi, category)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (r['timestamp'], r['station'], r['pm25'], r['pm10'], aqi, category))
                saved += 1
            except Exception as e:
                print(f"Error saving: {e}")
        
        conn.commit()
        conn.close()
        return saved
    
    def export_json(self):
        """Export readings to JSON for dashboard"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM measurements 
            ORDER BY timestamp DESC 
            LIMIT 100
        ''')
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        with open('data/latest_readings.json', 'w') as f:
            json.dump({
                'readings': data,
                'last_updated': datetime.now(UGANDA_TZ).isoformat(),
                'source': 'sample_data'
            }, f, indent=2, default=str)
        
        conn.close()
        return len(data)
    
    def run(self):
        """Main execution"""
        print("Fetching Gulu air quality data...")
        
        # Try to get real data first
        readings = self.fetch_from_airqo()
        
        # If no real data, use sample data
        if not readings:
            print("📊 Using sample data for Gulu City")
            readings = self.create_sample_data()
            source = "sample"
        else:
            source = "api"
        
        # Save to database
        saved = self.save_readings(readings)
        count = self.export_json()
        
        print(f"✅ Saved {saved} readings to database")
        print(f"📁 Exported {count} readings to JSON")
        
        # Show latest readings
        print("\n📊 Latest Readings:")
        for r in readings[:3]:
            category = self.get_category(r['pm25'])
            print(f"   {r['station']}: PM2.5 = {r['pm25']} µg/m³ ({category})")
        
        return readings


if __name__ == '__main__':
    monitor = GuluAirQuality()
    monitor.run()
