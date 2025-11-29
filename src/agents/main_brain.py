import logging
import json
from typing import Any, List
from src.agents.base_agent import BaseAgent, Signal
from src.data.groq_client import groq_client

logger = logging.getLogger(__name__)

class MainBrain(BaseAgent):
    def __init__(self):
        super().__init__("MainBrain")

    async def analyze(self, symbol: str, data: Any = None) -> Signal:
        """
        Aggregate signals from all agents and make a final trading decision.
        data: Expected to be a list of Signal objects from other agents.
        """
        try:
            if not data or not isinstance(data, list):
                logger.warning("MainBrain received invalid data (expected list of Signals)")
                return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0)

            # Prepare context for LLM
            signals_summary = []
            for s in data:
                signals_summary.append({
                    "agent": s.agent_name,
                    "action": s.action,
                    "confidence": s.confidence,
                    "metadata": s.metadata
                })
            
            signals_json = json.dumps(signals_summary, indent=2)
            
            prompt = f"""
            You are the Chief Investment Officer of a crypto trading fund.
            Your goal is to make a final BUY, SELL, or NEUTRAL decision for {symbol} based on the input signals from your team of specialized agents.
            
            Input Signals:
            {signals_json}
            
            Rules:
            1. Analyze the consensus among agents.
            2. **CRITICAL**: Some agents (like TechnicalAnalysisAgent) return action "ANALYSIS". For these, you MUST look at the 'metadata' (e.g., RSI, MACD values) and interpret them yourself.
               - RSI < 30 is generally Bullish (Oversold).
               - RSI > 70 is generally Bearish (Overbought).
               - MACD > Signal is Bullish.
            3. Weigh 'NewsSentimentAgent' and 'TrendFollowingAgent' higher than others.
            4. If signals are conflicting (e.g., Trend says BUY but News says BEARISH), prefer NEUTRAL or reduce confidence.
            5. Return your decision as a JSON object with keys: 'action', 'confidence', 'reasoning'.
            
            Example Output:
            {{
                "action": "BUY",
                "confidence": 0.85,
                "reasoning": "Technical indicators show RSI oversold (28) and MACD crossover. News is Bullish. Strong conviction."
            }}
            """
            
            messages = [
                {"role": "system", "content": "You are a high-stakes crypto trading AI. Output JSON only."},
                {"role": "user", "content": prompt}
            ]
            
            response_message = groq_client.query(
                messages=messages,
                model="openai/gpt-oss-120b",
                response_format={"type": "json_object"} # Enforce JSON
            )
            
            content = response_message.content
            logger.info(f"Main Brain Decision: {content}")
            
            decision = json.loads(content)
            
            return Signal(
                agent_name=self.name,
                symbol=symbol,
                action=decision.get("action", "NEUTRAL").upper(),
                confidence=float(decision.get("confidence", 0.0)),
                metadata={"reasoning": decision.get("reasoning", "")}
            )

        except Exception as e:
            logger.error(f"Main Brain analysis failed: {e}")
            return Signal(agent_name=self.name, symbol=symbol, action="NEUTRAL", confidence=0.0)
