"""
Flexible Agent Framework
Implements ReAct pattern (Think-Act-Observe)
"""
import logging
from typing import List, Dict, Any, Callable, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class Tool(BaseModel):
    """Tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable

class FlexibleAgent:
    """
    Base agent implementing ReAct pattern
    """
    
    def __init__(
        self,
        name: str,
        llm_client: Any,
        tools: List[Tool],
        max_iterations: int = 3  # Reduced from 10 for production efficiency
    ):
        self.name = name
        self.llm = llm_client
        self.tools = {t.name: t for t in tools}
        self.max_iterations = max_iterations
        self.context = {}  # Dynamic context (e.g., user_id, project_id)
        
    def _get_system_prompt(self) -> str:
        """Construct system prompt with tool definitions"""
        tool_descs = "\n".join([
            f"- {t.name}: {t.description}\n  Parameters: {t.parameters}"
            for t in self.tools.values()
        ])
        
        return f"""You are {self.name}, an AI assistant helping with academic literature reviews.

Available Tools:
{tool_descs}

CRITICAL INSTRUCTIONS:
1. For simple greetings or general questions, respond with ONLY:
{{"action": "Final Answer", "action_input": "Your friendly response here"}}

2. For tasks requiring tools, respond with ONLY:
{{"action": "tool_name", "action_input": {{"param": "value"}}}}

3. After using tools and having enough information, respond with ONLY:
{{"action": "Final Answer", "action_input": "Your complete answer based on observations"}}

RESPONSE FORMAT: Pure JSON only, no markdown, no explanation before or after.
BAD: "Let me help you..." or "Sure, I'll..."
GOOD: {{"action": "Final Answer", "action_input": "Hello! I'm your AI research assistant..."}}
"""

    async def run(self, input_text: str) -> Dict[str, Any]:
        """
        Run the agent loop (Think -> Act -> Observe)
        """
        history = [f"User: {input_text}"]
        last_action = None  # Track last action to prevent loops
        
        for i in range(self.max_iterations):
            # 1. THINK
            prompt = self._get_system_prompt() + "\n\nConversation:\n" + "\n".join(history) + "\n\nAssistant:"
            
            response = await self.llm.complete(
                prompt=prompt,
                temperature=0.1 # Low temp for tool selection
            )
            
            try:
                # Parse JSON response
                # LLMs explicitly asked for JSON but might wrap it in markdown
                cleaned_response = response.replace("```json", "").replace("```", "").strip()
                import json
                action_data = json.loads(cleaned_response)
                
                action = action_data.get("action")
                action_input = action_data.get("action_input")
                
                # Loop detection: Stop if trying same action twice in a row
                if action == last_action and action != "Final Answer":
                    logger.warning(f"🔁 Loop detected: '{action}' called twice. Forcing final answer.")
                    return {
                        "result": "I apologize, but I'm having trouble completing this task. Could you rephrase your question?",
                        "status": "loop_detected",
                        "steps": i+1
                    }
                last_action = action
                
                logger.info(f"🤔 Step {i+1}: Decision -> {action}")
                
            except Exception as e:
                # Failed to parse, treat as text response
                logger.warning(f"Failed to parse action: {e}. Raw response: {response[:200]}")
                # If this is a simple greeting/conversational message, just return it
                if i == 0 and len(response) < 500:
                    return {
                        "result": response, 
                        "status": "conversational", 
                        "steps": i+1
                    }
                # Otherwise log and continue
                history.append(f"Assistant response (unparsable): {response}")
                continue

            # 2. ACT
            if action == "Final Answer":
                return {
                    "result": action_input, 
                    "status": "success",
                    "steps": i+1
                }
            
            if action in self.tools:
                tool = self.tools[action]
                try:
                    # Execute tool - properly handle async
                    import inspect
                    if inspect.iscoroutinefunction(tool.function):
                        observation = await tool.function(**action_input)
                    else:
                        # Check if it's a lambda wrapping an async function
                        try:
                            result = tool.function(**action_input)
                            if inspect.iscoroutine(result):
                                observation = await result
                            else:
                                observation = result
                        except Exception as exec_err:
                            raise exec_err
                    
                    # 3. OBSERVE
                    result_str = f"Observation: {observation}"
                    history.append(f"Action: {action}\nInput: {action_input}\n{result_str}")
                    logger.info(f"👀 Observation: {str(observation)[:100]}...")
                    
                except Exception as e:
                    error_msg = str(e)[:200]  # Truncate long errors
                    history.append(f"Action: {action}\nError: {error_msg}")
                    logger.error(f"Tool execution failed: {e}")
            else:
                history.append(f"Error: Unknown tool '{action}'")
        
        return {
            "result": "I reached the maximum number of steps without a final answer.",
            "status": "max_iterations",
            "steps": self.max_iterations
        }
import asyncio
