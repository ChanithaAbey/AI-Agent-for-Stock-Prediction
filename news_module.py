import datetime
import os
import requests
from dotenv import load_dotenv
from typing import List, Dict, Optional
from datetime import datetime, timedelta

load_dotenv()

key = os.getenv("NEWS_API_KEY")

class NewsAgent:
    def __init__(self):
        self.api_token = key
        self.base_url = "https://api.thenewsapi.com/v1/news/all"

    def parse_date(self, date_str: str) -> Optional[datetime]:
        try:
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%8 %d, %Y'):
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception as e:
            print(f"Error parsing date: {str(e)}")
            return None
        
    def get_news(self, date_str: datetime, category: Optional[str] = None,
                 language: str = "en", max_results: int = 10, search_str: Optional[str] = None):
        
        published_on = date_str.strftime("%Y-%m-%d")
        params = {
            'api_token': self.api_token,
            'language': language,
            'published_on': published_on,
            'limit': max_results,
            'categories' : category,
            'search' : search_str
            
        }
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            return data
        
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'message': f"API request failed: {str(e)}",
            }

def main():
    
    agent = NewsAgent()

    result = agent.get_news("2024-12-26")
    rows = result['data']
    for row in rows:
        print(row['title'])
    
if __name__ == "__main__":
    main()