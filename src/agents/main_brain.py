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
            signal_summary = "\n".join(
                [f"- {s.agent_name}: {s.action} (Conf: {s.confidence:.2f}) | {s.metadata}" for s in data]
            )

            # 2. RAG: Recall "The Past" (The Vector DB Connection)
            # We assume the Technical Agent's metadata contains a 'vector' or we build a pseudo-vector string
            # For simplicity, we search memory using a text description of the strongest signal
            # strongest_signal = max(signals, key=lambda s: s.confidence)
            # query_context = f"{strongest_signal.agent_name} says {strongest_signal.action} with {strongest_signal.metadata}"
            
            # RECALL MEMORY (The "Spark Plug")
            # In a real system, we'd generate an embedding here: vector = get_embedding(signal_summary)
            # For now, we log the intent.
            # past_wisdom = await db_manager.recall_similar_situations(vector)
            # if past_wisdom:
            #     prompt += f"\n\nHISTORICAL PRECEDENT:\n{past_wisdom}"

            prompt = f"""
            You are the Head Trader of a Crypto Hedge Fund.
            
            CURRENT MARKET DATA (The "Now"):
            {signal_summary}
            
            TASK:
            Analyze the conflicting signals. 
            - Technical Analysis provides the raw stats.
            - Sentiment provides the news.
            - Whales provide the flow.
            
            DECISION LOGIC:
            - If Whales BUY + Tech OVERSOLD -> STRONG BUY
            - If News FUD + Tech OVERBOUGHT -> STRONG SELL
            - If signals conflict -> NEUTRAL (Preserve Capital)
            
            Return JSON: {{ "action": "BUY/SELL/NEUTRAL", "confidence": 0.0-1.0, "reasoning": "..." }}
            """

            # Call Groq
            response = groq_client.query(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-70b-8192", # Use a smart model
                temperature=0.1
            )
            
            # Parse
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            
            decision = json.loads(content)
            
            # 4. STORE THIS THOUGHT (Save to Memory)
            # We save the "Scenario" so we can remember it later
            # (In V2, we generate an embedding here)
            # Import db_manager here to avoid circular import if needed, or rely on top-level
            from src.data.db_manager import db_manager
            await db_manager.store_thought(
                symbol=symbol, 
                vector=None, # Placeholder until embedding model is added
                description=f"Signals: {signal_summary[:200]}... Result: {decision.get('action')}"
            )

            return Signal(
                agent_name="MainBrain",
                symbol=symbol,
                action=decision.get("action", "NEUTRAL").upper(),
                confidence=float(decision.get("confidence", 0.0)),
                metadata={"reasoning": decision.get("reasoning", "")}
            )

        except Exception as e:
            logger.error(f"Brain Lobotomy Error: {e}")
            return Signal("MainBrain", symbol, "NEUTRAL", 0.0, {"error": str(e)})
