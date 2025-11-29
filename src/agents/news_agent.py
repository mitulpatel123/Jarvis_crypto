import logging
import json
from typing import Any
from src.agents.base_agent import BaseAgent, Signal
from src.data.groq_client import groq_client

logger = logging.getLogger(__name__)

class NewsSentimentAgent(BaseAgent):
    def __init__(self):
        super().__init__("NewsSentimentAgent")

    async def analyze(self, symbol: str, data: Any = None) -> Signal:
        """
        Analyze news sentiment for the symbol using Groq Browser Automation.
        """
        try:
            query = f"Search for the latest news and market sentiment for {symbol} (crypto) from reliable sources like CoinDesk, Cointelegraph, and The Block. Summarize the overall sentiment as BULLISH, BEARISH, or NEUTRAL and provide a confidence score (0.0 to 1.0). Return the result as JSON with keys: 'sentiment', 'confidence', 'summary'."
            
            messages = [{"role": "user", "content": query}]
            
            # Use compound-mini with browser automation
            # Note: We don't pass 'tools' list for built-in tools in compound_custom, 
            # we just enable them.
            
            response_message = groq_client.query(
                messages=messages,
                model="groq/compound-mini",
                extra_body={
                    "compound_custom": {
                        "tools": {
                            "enabled_tools": ["browser_automation", "web_search"]
                        }
                    }
                }
            )
            
            content = response_message.content
            logger.info(f"News Agent Response: {content}")
            
            # Parse response (expecting JSON or structured text)
            # Since the model might return text, we'll try to parse or use a regex/heuristic
            # For robustness, we could ask for JSON format specifically in system prompt.
            
            action = "NEUTRAL"
            confidence = 0.5
            summary = content
            
            if "BULLISH" in content.upper():
                action = "BUY"
                confidence = 0.7
            elif "BEARISH" in content.upper():
                action = "SELL"
                confidence = 0.7
                
            # Try to extract confidence if explicit
            # (Simple heuristic for now)
            
            return Signal(
                agent_name=self.name,
                symbol=symbol,
                action=action,
                confidence=confidence,
                metadata={"summary": summary[:200] + "..."}
            )

        except Exception as e:
            logger.error(f"News analysis failed: {e}")
            return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0)
