import sqlite3
import json
import os

DB_PATH = r'c:\Users\Sebastian\Desktop\GoFundBot\MyBot\Data\funds.db'

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check daily_market_summary
        cursor.execute("SELECT date, detailed_analysis_json, hot_sectors_json FROM daily_market_summary ORDER BY date DESC LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            date, detailed_json, hot_sectors = row
            print(f"Date: {date}")
            print(f"Hot Sectors: {hot_sectors}")
            print(f"Detailed Analysis (Raw): {detailed_json}")
            
            if detailed_json:
                try:
                    data = json.loads(detailed_json)
                    print(f"Detailed Analysis (Parsed): {json.dumps(data, indent=2, ensure_ascii=False)}")
                except:
                    print("Detailed Analysis JSON parse failed")
            else:
                print("Detailed Analysis is NULL or Empty")
        else:
            print("No records found in daily_market_summary")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_db()
