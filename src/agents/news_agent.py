from src.agents.base_agent import BaseAgent, Signal
from src.data.groq_client import groq_client
import json
from typing import Any

class NewsSentimentAgent(BaseAgent):
    def __init__(self):
        super().__init__("NewsSentimentAgent")

    async def analyze(self, symbol: str, data: Any = None) -> Signal:
        # 1. Define Search Query
        query = f"latest crypto news {symbol} price analysis bullish bearish"
        
        # 2. Ask Groq to "Browse" (Simulated via LLM knowledge + context if available)
        # Note: Ideally you feed real headlines here. 
        # Since we don't have a news scraper in the file list, we use Groq's internal knowledge 
        # or assume 'data' contains headlines.
        
        prompt = f"""
        Analyze the sentiment for {symbol} based on recent market trends.
        Return JSON: {{ "sentiment": "BULLISH/BEARISH/NEUTRAL", "confidence": 0.0-1.0, "summary": "..." }}
        """
        
        try:
            response = groq_client.query([{"role": "user", "content": prompt}])
            content = response.content.strip()
            # Clean json
            if "```" in content: content = content.split("```json")[1].split("```")[0]
            
            result = json.loads(content)
            
            action_map = {"BULLISH": "BUY", "BEARISH": "SELL", "NEUTRAL": "NEUTRAL"}
            
            return Signal(
                self.name, 
                symbol, 
                action_map.get(result.get("sentiment", "NEUTRAL"), "NEUTRAL"),
                float(result.get("confidence", 0.5)),
                {"summary": result.get("summary")}
            )
        except Exception as e:
            return Signal(self.name, symbol, "NEUTRAL", 0.0, {"error": str(e)})
