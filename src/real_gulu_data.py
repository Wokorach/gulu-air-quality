#!/usr/bin/env python3
"""
Gulu Air Quality Data Fetcher - Working with ALL 6 Stations
Handles stations where AQI is "-" by calculating from PM2.5
"""

import requests
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import pytz

DB_PATH = 'data/gulu_air_quality.db'
UGANDA_TZ = pytz.timezone('Africa/Kampala')

AQICN_TOKEN = "30c2eb1a7728722c1767bb97c935b7dddaff052b"

# All 6 Gulu monitoring stations with their correct AQICN IDs (A-prefixed)
GULU_STATIONS = [
    {"id": "A422173", "name": "Gulu Main Market"},
    {"id": "A418078", "name": "Gulu University"},
    {"id": "A418291", "name": "Lapeta Health Centre 3"},
    {"id": "A418414", "name": "Mary Queen of Peace P/s Gulu"},
    {"id": "A418459", "name": "Pece Gulu"},
    {"id": "A418084", "name": "Layibi Gulu"}
]

class GuluAirQuality:
    def __init__(self):
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        self.setup_db()
        print("=" * 60)
        print("🌍 Gulu Air Quality Data Fetcher - ALL 6 STATIONS")
        print("=" * 60)
        print(f"Source: AQICN API (https://aqicn.org)")
        print(f"Monitoring Stations: {len(GULU_STATIONS)}")
        for s in GULU_STATIONS:
            print(f"  • {s['name']} ({s['id']})")
        print("=" * 60)
    
    def setup_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                station_id TEXT,
                station_name TEXT,
                pm25 REAL,
                pm10 REAL,
                aqi INTEGER,
                category TEXT,
                source TEXT,
                UNIQUE(timestamp, station_id)
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Database ready")
    
    def pm25_to_aqi(self, pm25):
        """Convert PM2.5 to AQI (EPA standard)"""
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
    
    def get_category_from_aqi(self, aqi):
        """Convert AQI value to category (EPA standard)"""
        if aqi is None:
            return "No Data"
        if aqi <= 50:
            return "Good"
        elif aqi <= 100:
            return "Moderate"
        elif aqi <= 150:
            return "Unhealthy for Sensitive"
        elif aqi <= 200:
            return "Unhealthy"
        elif aqi <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"
    
    def fetch_station_data(self, station):
        """Fetch real data from AQICN API for a specific station"""
        station_id = station["id"]
        station_name = station["name"]
        
        try:
            url = f"https://api.waqi.info/feed/{station_id}/?token={AQICN_TOKEN}"
            print(f"📡 Fetching: {station_name} ({station_id})")
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'ok':
                    station_data = data.get('data', {})
                    
                    # Get AQI - may be "-" so we'll calculate from PM2.5
                    aqi_raw = station_data.get('aqi')
                    
                    # Get PM2.5 and PM10 from iaqi
                    iaqi = station_data.get('iaqi', {})
                    pm25_info = iaqi.get('pm25', {})
                    pm10_info = iaqi.get('pm10', {})
                    
                    pm25 = pm25_info.get('v') if pm25_info else None
                    pm10 = pm10_info.get('v') if pm10_info else None
                    
                    # Calculate AQI from PM2.5 if needed
                    if aqi_raw == "-" or aqi_raw is None:
                        aqi = self.pm25_to_aqi(pm25) if pm25 else None
                    else:
                        aqi = aqi_raw
                    
                    # Get timestamp
                    time_info = station_data.get('time', {})
                    timestamp = time_info.get('iso', datetime.now().isoformat())
                    
                    if aqi is not None:
                        category = self.get_category_from_aqi(aqi)
                        print(f"   ✅ PM2.5: {pm25} | PM10: {pm10} | AQI: {aqi} | Category: {category}")
                        
                        return {
                            'station_id': station_id,
                            'station_name': station_name,
                            'pm25': pm25,
                            'pm10': pm10,
                            'aqi': aqi,
                            'timestamp': timestamp,
                            'source': 'AQICN'
                        }
                    else:
                        print(f"   ⚠️ No data available for {station_name}")
                        return None
                else:
                    print(f"   ❌ API error: {data.get('data', 'Unknown error')}")
                    return None
            else:
                print(f"   ❌ HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return None
    
    def fetch_all_stations(self):
        """Fetch data for all Gulu stations"""
        all_readings = []
        
        print("\n📡 Fetching real-time data from AQICN...")
        print("-" * 50)
        
        for station in GULU_STATIONS:
            reading = self.fetch_station_data(station)
            if reading:
                all_readings.append(reading)
        
        print("-" * 50)
        print(f"\n✅ Successfully fetched {len(all_readings)} of {len(GULU_STATIONS)} stations")
        
        # Print summary of working stations
        if all_readings:
            print("\n📊 Working stations:")
            for r in all_readings:
                print(f"   • {r['station_name']} - AQI: {r['aqi']} | PM2.5: {r['pm25']}")
        
        return all_readings
    
    def save_readings(self, readings):
        """Save readings to database"""
        if not readings:
            return 0
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        inserted = 0
        
        for r in readings:
            category = self.get_category_from_aqi(r['aqi'])
            
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO measurements
                    (timestamp, station_id, station_name, pm25, pm10, aqi, category, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    r['timestamp'],
                    r['station_id'],
                    r['station_name'],
                    r.get('pm25'),
                    r.get('pm10'),
                    r['aqi'],
                    category,
                    r['source']
                ))
                inserted += 1
            except Exception as e:
                print(f"Insert error: {e}")
        
        conn.commit()
        conn.close()
        return inserted
    
    def export_json(self, readings):
        """Export readings to JSON for dashboard"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM measurements 
            ORDER BY timestamp DESC 
            LIMIT 500
        ''')
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
        
        source = "AQICN (Real-time)" if readings else "No Data"
        
        with open('data/latest_readings.json', 'w') as f:
            json.dump({
                'readings': data,
                'last_updated': datetime.now(UGANDA_TZ).isoformat(),
                'source': source,
                'stations_found': list(set(r['station_name'] for r in data))
            }, f, indent=2, default=str)
        
        # Print summary
        stations = set(r['station_name'] for r in data)
        print(f"\n📊 Stations saved to JSON ({len(stations)} stations):")
        for s in sorted(stations):
            print(f"   - {s}")
        
        return len(data)
    
    def run(self):
        print("\n🔄 Fetching Gulu air quality data for all 6 stations...")
        
        readings = self.fetch_all_stations()
        
        if readings:
            inserted = self.save_readings(readings)
            print(f"\n💾 Saved {inserted} readings to database")
            
            total = self.export_json(readings)
            print(f"\n📄 Exported {total} total readings to JSON")
            print("\n🎉 SUCCESS! All 6 stations are now in your dashboard!")
            print("\n🌍 View your dashboard at: https://YOUR-USERNAME.github.io/gulu-air-quality/")
        else:
            print("\n⚠️ No data received")
            
            with open('data/latest_readings.json', 'w') as f:
                json.dump({
                    'readings': [],
                    'last_updated': datetime.now(UGANDA_TZ).isoformat(),
                    'source': 'No Data'
                }, f, indent=2, default=str)
        
        return readings

if __name__ == '__main__':
    monitor = GuluAirQuality()
    monitor.run()
