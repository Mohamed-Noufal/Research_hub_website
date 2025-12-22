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
        max_iterations: int = 10
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
        
        return f"""You are {self.name}, an AI research assistant.
You have access to the following tools:

{tool_descs}

To use a tool, output ONLY a JSON block like this:
{{
    "action": "tool_name",
    "action_input": {{ "param": "value" }}
}}

When you have the final answer, output:
{{
    "action": "Final Answer",
    "action_input": "Your response here"
}}

Refuse to answer if outside your scope.
"""

    async def run(self, input_text: str) -> Dict[str, Any]:
        """
        Run the agent loop (Think -> Act -> Observe)
        """
        history = [f"User: {input_text}"]
        
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
                
                logger.info(f"🤔 Step {i+1}: Decision -> {action}")
                
            except Exception as e:
                # Failed to parse, treat as text response
                logger.warning(f"Failed to parse action: {e}. Raw: {response}")
                # If it looks like a final answer (no JSON), just return it
                return {"result": response, "status": "conversational", "steps": i+1}

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
                    # Execute tool
                    # Pass agent context if needed by tool (implicitly handling kwargs)
                    # For simplicity, passing kwargs matching function sig
                    # In production, inspect function sig to match args safer
                    observation = await tool.function(**action_input) if asyncio.iscoroutinefunction(tool.function) else tool.function(**action_input)
                    
                    # 3. OBSERVE
                    result_str = f"Observation: {observation}"
                    history.append(f"Action: {action}\nInput: {action_input}\n{result_str}")
                    logger.info(f"👀 Observation: {str(observation)[:100]}...")
                    
                except Exception as e:
                    history.append(f"Action: {action}\nError: {str(e)}")
                    logger.error(f"Tool execution failed: {e}")
            else:
                history.append(f"Error: Unknown tool '{action}'")
        
        return {
            "result": "I reached the maximum number of steps without a final answer.",
            "status": "max_iterations",
            "steps": self.max_iterations
        }
import asyncio
