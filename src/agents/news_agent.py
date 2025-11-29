from src.agents.base_agent import BaseAgent, Signal
from src.data.groq_client import groq_client
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

class NewsSentimentAgent(BaseAgent):
    def __init__(self):
        super().__init__("NewsSentimentAgent")

    async def analyze(self, symbol: str, data: Any = None) -> Signal:
        """
        Searches for recent news about the symbol and analyzes sentiment using Groq.
        """
        try:
            from googlesearch import search
        except ImportError:
            logger.error("googlesearch-python not installed. Cannot fetch news.")
            return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0, metadata={"error": "Missing dependency"})

        # 1. Search for News
        query = f"crypto news {symbol} price analysis bullish bearish"
        news_titles = []
        try:
            # Fetch top 5 results
            for result in search(query, num_results=5, advanced=True):
                news_titles.append(f"{result.title}: {result.description}")
        except Exception as e:
            logger.warning(f"News search failed: {e}")
            return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0, metadata={"error": "Search failed"})

        if not news_titles:
            return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0, metadata={"status": "No news found"})

        # 2. Analyze Sentiment with Groq
        news_text = "\n".join(news_titles)
        prompt = f"""
        Analyze the sentiment for {symbol} based on these recent news headlines/snippets:
        {news_text}
        
        Return JSON: {{ "sentiment": "BULLISH/BEARISH/NEUTRAL", "confidence": 0.0-1.0, "summary": "Brief summary of news" }}
        """
        
        try:
            response = groq_client.query([{"role": "user", "content": prompt}])
            content = response.content.strip()
            # Clean json
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content)
            
            action_map = {"BULLISH": "BUY", "BEARISH": "SELL", "NEUTRAL": "NEUTRAL"}
            action = action_map.get(result.get("sentiment", "NEUTRAL").upper(), "NEUTRAL")
            
            return Signal(
                agent_name=self.name, 
                symbol=symbol, 
                action=action,
                confidence=float(result.get("confidence", 0.5)),
                metadata={"summary": result.get("summary", ""), "headlines": news_titles[:2]}
            )
        except Exception as e:
            logger.error(f"News analysis failed: {e}")
            return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0, metadata={"error": str(e)})
