import sys
import os
from datetime import datetime

# Add Backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_service import get_llm_service

def refresh():
    print("Starting manual refresh...")
    try:
        service = get_llm_service()
        if not service.is_available():
            print("LLM Service not available (check API keys)")
            return

        today_key = datetime.now().strftime("%Y-%m-%d")
        today_str = datetime.now().strftime("%Y年%m月%d日")
        
        print(f"Regenerating for {today_str}...")
        
        # Manually trigger the generation
        service._update_progress(today_key, 1, '正在根据新模型重新分析市场...')
        result = service._do_generate_market_summary(today_key, today_str)
        
        if 'error' in result:
            service._save_market_summary(today_key, None, status='error', error=result['error'])
            print(f"Error: {result['error']}")
        else:
            service._save_market_summary(today_key, result, status='completed')
            print("Market summary updated successfully!")
            
    except Exception as e:
        print(f"Exception during refresh: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    refresh()
