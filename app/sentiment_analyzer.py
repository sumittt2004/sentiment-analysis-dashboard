"""Sentiment Analysis Module"""

import os
import torch
from transformers import pipeline
from typing import List, Dict
import pandas as pd
from loguru import logger
from diskcache import Cache
import hashlib

cache = Cache('./data/cache')

class SentimentAnalyzer:
    """Sentiment analyzer using DistilBERT"""
    
    def __init__(self):
        self.model_name = os.getenv('MODEL_NAME', 'distilbert-base-uncased-finetuned-sst-2-english')
        self.device = 0 if torch.cuda.is_available() else -1
        self.batch_size = int(os.getenv('BATCH_SIZE', 10))
        self.model_cache_dir = './models'  # Store models in project folder
        
        # Create models directory if it doesn't exist
        os.makedirs(self.model_cache_dir, exist_ok=True)
        
        logger.info(f"Loading model: {self.model_name}")
        logger.info(f"Model cache directory: {self.model_cache_dir}")
        logger.info(f"Device: {'GPU' if self.device == 0 else 'CPU'}")
        
        try:
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                device=self.device,
                truncation=True,
                max_length=512,
                model_kwargs={'cache_dir': self.model_cache_dir}
            )
            logger.info("✅ Model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            raise
    
    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Analyze multiple texts"""
        
        if not texts:
            return []
        
        results = []
        
        try:
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                batch = [str(text)[:512] if text else "" for text in batch]
                
                batch_results = self.pipeline(batch)
                
                for result in batch_results:
                    sentiment_score = result['score'] if result['label'] == 'POSITIVE' else -result['score']
                    
                    results.append({
                        'label': result['label'],
                        'score': result['score'],
                        'sentiment': sentiment_score
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return [{'label': 'NEUTRAL', 'score': 0.0, 'sentiment': 0.0}] * len(texts)
    
    def analyze_dataframe(self, df: pd.DataFrame, text_column: str = 'text') -> pd.DataFrame:
        """Analyze sentiment for DataFrame"""
        
        if df.empty or text_column not in df.columns:
            logger.warning(f"DataFrame is empty or '{text_column}' not found")
            return df
        
        logger.info(f"Analyzing sentiment for {len(df)} items...")
        
        texts = df[text_column].fillna('').tolist()
        results = self.analyze_batch(texts)
        
        df['sentiment_label'] = [r['label'] for r in results]
        df['sentiment_score'] = [r['score'] for r in results]
        df['sentiment'] = [r['sentiment'] for r in results]
        
        df['sentiment_category'] = df['sentiment'].apply(
            lambda x: 'Positive' if x > 0.2 else ('Negative' if x < -0.2 else 'Neutral')
        )
        
        logger.info("✅ Sentiment analysis complete")
        
        dist = df['sentiment_category'].value_counts().to_dict()
        logger.info(f"Distribution: {dist}")
        
        return df
    
    def get_summary_statistics(self, df: pd.DataFrame) -> Dict:
        """Calculate summary stats"""
        
        if df.empty or 'sentiment' not in df.columns:
            return {}
        
        return {
            'total_items': len(df),
            'positive_count': len(df[df['sentiment'] > 0.2]),
            'negative_count': len(df[df['sentiment'] < -0.2]),
            'neutral_count': len(df[df['sentiment'].between(-0.2, 0.2)]),
            'avg_sentiment': df['sentiment'].mean(),
            'positive_ratio': len(df[df['sentiment'] > 0.2]) / len(df) * 100,
            'negative_ratio': len(df[df['sentiment'] < -0.2]) / len(df) * 100
        }


if __name__ == "__main__":
    logger.info("Testing sentiment analyzer...")
    
    analyzer = SentimentAnalyzer()
    
    test_texts = [
        "This is absolutely amazing! I love it!",
        "Terrible experience, would not recommend.",
        "It's okay, nothing special."
    ]
    
    results = analyzer.analyze_batch(test_texts)
    
    print("\n✅ Sentiment Analysis Results:")
    for text, result in zip(test_texts, results):
        print(f"\nText: {text}")
        print(f"Sentiment: {result['label']} (score: {result['sentiment']:.2f})")