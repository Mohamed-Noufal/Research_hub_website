"""
Flexible Agent Framework
Implements ReAct pattern (Think-Act-Observe) with streaming support
"""
import logging
from typing import List, Dict, Any, Callable, Optional, AsyncGenerator
from pydantic import BaseModel
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from app.core.monitoring import get_tracer

logger = logging.getLogger(__name__)

class Tool(BaseModel):
    """Tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable

class FlexibleAgent:
    """
    Base agent implementing ReAct pattern with streaming
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
        
        # Add context information if available
        context_info = ""
        if self.context:
            if 'project_id' in self.context:
                context_info = f"\n\nCurrent Context:\n- Project ID: {self.context['project_id']}\n- User ID: {self.context.get('user_id', 'unknown')}"
        
        return f"""You are {self.name}, an AI assistant specialized in academic literature review.

{context_info}

Available Tools:
{tool_descs}

DECISION RULES:
1. If user asks about papers, methodology, findings, or comparisons → USE TOOLS
   Examples that REQUIRE tools:
   - "Show me methodology for paper X" → use extract_methodology
   - "What papers are in this project?" → use get_project_papers  
   - "Compare these papers" → use compare_papers
   - "Search for X topic" → use semantic_search

2. If user asks simple questions or greetings → DIRECT ANSWER
   Examples: "Hi", "How are you?", "What can you do?"

3. After getting tool results → SYNTHESIZE and give Final Answer

MULTI-STEP REASONING:
You can chain multiple actions together intelligently:

Example 1 - Check before extracting:
User: "Extract methodology from papers in project 5"
Step 1: {{"action": "get_project_papers", "action_input": {{"project_id": 5}}}}
[Observe: Returns papers with is_processed status]
Step 2: If paper is_processed=False → {{"action": "parse_pdf", "action_input": {{"paper_id": X, "pdf_path": "..."}}}}
Step 3: {{"action": "check_job_status", "action_input": {{"job_id": "..."}}}}
Step 4: Once processed → {{"action": "extract_methodology", "action_input": {{"paper_id": X}}}}
Step 5: {{"action": "Final Answer", "action_input": "Here's the methodology: ..."}}

Example 2 - Inform user about processing:
If paper is NOT processed yet:
{{"action": "Final Answer", "action_input": "I found the paper, but it hasn't been processed yet. I've started parsing it in the background (Job ID: XXX). This usually takes 1-2 minutes. Please check back shortly or ask me to check the status."}}

RESPONSE FORMAT (CRITICAL):
You MUST respond with ONLY valid JSON. No text before or after.

For tool use:
{{"action": "tool_name", "action_input": {{"param": "value"}}}}

For final answer:
{{"action": "Final Answer", "action_input": "Your complete response here"}}

EXAMPLES:
User: "Extract methodology from paper 1"
You: {{"action": "extract_methodology", "action_input": {{"paper_id": 1}}}}

User: "What papers are in project 5?"
You: {{"action": "get_project_papers", "action_input": {{"project_id": 5}}}}

User: "What papers are in Test 1 project?"
Step 1: {{"action": "get_project_by_name", "action_input": {{"project_name": "Test 1", "user_id": "[from context]"}}}}
[Observe: Returns {{"id": 5, "name": "Test 1", ...}}]
Step 2: {{"action": "get_project_papers", "action_input": {{"project_id": 5}}}}
[Observe: Returns list of papers]
Step 3: {{"action": "Final Answer", "action_input": "I found 3 papers in Test 1 project: ..."}}

User: "Hello"
You: {{"action": "Final Answer", "action_input": "Hello! I'm your AI research assistant. I can help you explore methodologies, compare papers, and analyze your literature review."}}
"""

    async def run_streaming(self, input_text: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run the agent loop with streaming events (Think -> Act -> Observe)
        Yields status updates for UI display
        """
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span(f"AgentRun.{self.name}") as run_span:
            history = [f"User: {input_text}"]
            last_action = None
            
            for i in range(self.max_iterations):
                # 1. THINK
                yield {"type": "thinking", "step": i+1, "message": "Analyzing your request..."}
                
                with tracer.start_as_current_span(f"Think_Step_{i+1}") as think_span:
                    prompt = self._get_system_prompt() + "\n\nConversation:\n" + "\n".join(history) + "\n\nAssistant:"
                    
                    response = await self.llm.complete(
                        prompt=prompt,
                        temperature=0.1
                    )
                    think_span.set_attribute("llm.response", response)
                
                try:
                    # Parse JSON response
                    cleaned_response = response.replace("```json", "").replace("```", "").strip()
                    import json
                    action_data = json.loads(cleaned_response)
                    
                    action = action_data.get("action")
                    action_input = action_data.get("action_input")
                    
                    run_span.add_event(f"Decision_Made", attributes={"action": action, "step": i+1})
                    
                    # Loop detection
                    if action == last_action and action != "Final Answer":
                        logger.warning(f"🔁 Loop detected: '{action}' called twice.")
                        run_span.set_status(Status(StatusCode.ERROR, "Loop detected"))
                        yield {
                            "type": "error",
                            "message": "I'm having trouble completing this task. Could you rephrase your question?"
                        }
                        return
                    last_action = action
                    
                    logger.info(f"🤔 Step {i+1}: Decision -> {action}")
                    
                except Exception as e:
                    logger.warning(f"Failed to parse action: {e}")
                    if i == 0 and len(response) < 500:
                        yield {"type": "message", "content": response}
                        return
                    history.append(f"Assistant response (unparsable): {response}")
                    continue

                # 2. ACT
                if action == "Final Answer":
                    yield {"type": "synthesizing", "message": "Generating final answer..."}
                    yield {"type": "message", "content": action_input}
                    return
                
                if action in self.tools:
                    tool = self.tools[action]
                    
                    # Emit tool selection event
                    yield {
                        "type": "tool_selected",
                        "tool": action,
                        "parameters": action_input,
                        "step": i+1
                    }
                    
                    with tracer.start_as_current_span(f"Act_Step_{i+1}") as act_span:
                        act_span.set_attribute("tool.name", action)
                        act_span.set_attribute("tool.input", str(action_input))
                        
                        # Emit executing event
                        yield {"type": "tool_executing", "tool": action}
                        
                        try:
                            # Execute tool
                            import inspect
                            if inspect.iscoroutinefunction(tool.function):
                                observation = await tool.function(**action_input)
                            else:
                                result = tool.function(**action_input)
                                if inspect.iscoroutine(result):
                                    observation = await result
                                else:
                                    observation = result
                            
                            # Emit result event
                            yield {
                                "type": "tool_result",
                                "tool": action,
                                "result": observation
                            }
                            
                            result_str = f"Observation: {observation}"
                            history.append(f"Action: {action}\nInput: {action_input}\n{result_str}")
                            logger.info(f"👀 Observation: {str(observation)[:100]}...")
                            act_span.set_attribute("tool.output", str(observation)[:500])
                            
                        except Exception as e:
                            error_msg = str(e)[:200]
                            history.append(f"Action: {action}\nError: {error_msg}")
                            logger.error(f"Tool execution failed: {e}")
                            act_span.set_status(Status(StatusCode.ERROR, str(e)))
                            act_span.record_exception(e)
                            
                            yield {
                                "type": "tool_error",
                                "tool": action,
                                "error": error_msg
                            }
                else:
                    history.append(f"Error: Unknown tool '{action}'")
                    yield {"type": "error", "message": f"Unknown tool: {action}"}
            
            run_span.set_status(Status(StatusCode.ERROR, "Max iterations reached"))
            yield {
                "type": "error",
                "message": "I reached the maximum number of steps without a final answer."
            }

    async def run(self, input_text: str) -> Dict[str, Any]:
        """
        Non-streaming version for backward compatibility
        """
        result_content = None
        status = "unknown"
        steps = 0
        
        async for event in self.run_streaming(input_text):
            steps += 1
            if event["type"] == "message":
                result_content = event["content"]
                status = "success"
            elif event["type"] == "error":
                result_content = event["message"]
                status = "error"
        
        return {
            "result": result_content or "No response generated",
            "status": status,
            "steps": steps
        }

import asyncio
