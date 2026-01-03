"""Data Collection Module"""

import os
import time
from datetime import datetime, timedelta
from typing import List, Dict
from newsapi import NewsApiClient
from loguru import logger
from diskcache import Cache
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
cache = Cache('./data/cache')

class NewsCollector:
    """Collects news articles"""
    
    def __init__(self):
        self.api_key = os.getenv('NEWS_API_KEY')
        if not self.api_key:
            logger.error("NEWS_API_KEY not found in .env file!")
            self.client = None
        else:
            self.client = NewsApiClient(api_key=self.api_key)
            logger.info("News API client initialized")
    
    def search_news(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search news articles"""
        
        if not self.client:
            logger.error("News API client not initialized")
            return []
        
        cache_key = f"news_{query}_{max_results}"
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Returning {len(cached)} cached articles")
            return cached
        
        try:
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            logger.info(f"Searching news for: {query}")
            response = self.client.get_everything(
                q=query,
                from_param=from_date,
                language='en',
                sort_by='publishedAt',
                page_size=min(max_results, 100)
            )
            
            if not response.get('articles'):
                logger.warning(f"No articles found for: {query}")
                return []
            
            articles = []
            for article in response['articles']:
                articles.append({
                    'title': article['title'],
                    'text': article.get('description', '') or article.get('content', ''),
                    'created_at': datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'),
                    'source': f"news_{article['source']['name']}",
                    'url': article['url']
                })
            
            cache.set(cache_key, articles, expire=3600)
            logger.info(f"Collected {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return []


class DataCollector:
    """Main data collector"""
    
    def __init__(self):
        self.news = NewsCollector()
    
    def collect_data(self, query: str, max_results: int = 50) -> pd.DataFrame:
        """Collect data from news"""
        
        articles = self.news.search_news(query, max_results)
        
        if not articles:
            logger.warning("No data collected")
            return pd.DataFrame()
        
        df = pd.DataFrame(articles)
        df['query'] = query
        df['collected_at'] = datetime.now()
        
        logger.info(f"Total items collected: {len(df)}")
        return df


if __name__ == "__main__":
    collector = DataCollector()
    df = collector.collect_data("artificial intelligence", max_results=20)
    
    if not df.empty:
        print(f"\n✅ SUCCESS! Collected {len(df)} articles")
        print(df[['title', 'source']].head())
    else:
        print("\n❌ No data collected. Check your API key!")