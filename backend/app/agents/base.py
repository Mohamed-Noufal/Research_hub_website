"""
Flexible Agent Framework
Implements ReAct pattern (Think-Act-Observe) with streaming support
"""
import logging
from typing import List, Dict, Any, Callable, Optional, AsyncGenerator
from pydantic import BaseModel
from app.core.config import settings
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind
from app.core.monitoring import get_tracer

# OpenInference semantic conventions for Phoenix
OPENINFERENCE_SPAN_KIND = "openinference.span.kind"
INPUT_VALUE = "input.value"
OUTPUT_VALUE = "output.value"
LLM_MODEL_NAME = "llm.model_name"
LLM_INPUT_MESSAGES = "llm.input_messages"
LLM_OUTPUT_MESSAGES = "llm.output_messages"
TOOL_NAME = "tool.name"
TOOL_PARAMETERS = "tool.parameters"

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
        max_iterations: int = None  # Defaults to settings.AGENT_MAX_ITERATIONS
    ):
        self.name = name
        self.llm = llm_client
        self.tools = {t.name: t for t in tools}
        self.max_iterations = max_iterations if max_iterations is not None else settings.AGENT_MAX_ITERATIONS
        self.context = {}  # Dynamic context (e.g., user_id, project_id)
    
    def _update_active_context(self, action: str, observation: Any):
        """
        Extract and update active context from tool observations.
        This helps the agent avoid redundant lookups in subsequent turns.
        """
        if not self.context or 'active_context' not in self.context:
            return  # No active context to update
        
        active_ctx = self.context['active_context']
        
        try:
            # Handle get_project_by_name results
            if action == 'get_project_by_name':
                if isinstance(observation, dict) and 'id' in observation:
                    active_ctx['current_project'] = {
                        'id': observation.get('id'),
                        'name': observation.get('title') or observation.get('name', 'Unknown')
                    }
                    logger.info(f"📌 Active context: Set current_project = {active_ctx['current_project']}")
            
            # Handle get_project_papers results
            elif action == 'get_project_papers':
                if isinstance(observation, list):
                    # Store resolved papers for quick reference
                    active_ctx['resolved_papers'] = [
                        {'id': p.get('id'), 'title': p.get('title', 'Unknown')[:50]}
                        for p in observation[:5]  # Keep top 5
                    ]
                    # If only one paper, set as current
                    if len(observation) == 1:
                        active_ctx['current_paper'] = {
                            'id': observation[0].get('id'),
                            'title': observation[0].get('title', 'Unknown')
                        }
                    logger.info(f"📌 Active context: Resolved {len(active_ctx['resolved_papers'])} papers")
            
            # Handle extract_methodology, extract_findings - set current paper if paper_id in input
            elif action in ['extract_methodology', 'extract_findings', 'get_paper_sections']:
                # These tools work on a specific paper, note it as current
                # The input was action_input which we don't have here, but observation often contains paper info
                if isinstance(observation, dict) and 'paper_id' in str(observation):
                    pass  # Paper ID is implicit from the call
                    
        except Exception as e:
            logger.warning(f"Failed to update active context: {e}")
        
    def _get_system_prompt(self) -> str:
        """Construct system prompt with tool definitions"""
        tool_descs = "\n".join([
            f"- {t.name}: {t.description}\n  Parameters: {t.parameters}"
            for t in self.tools.values()
        ])
        
        # Add context information if available
        context_info = ""
        active_context_info = ""
        
        if self.context:
            scope = self.context.get('scope', 'library')
            selected_paper_ids = self.context.get('selected_paper_ids', [])
            project_id = self.context.get('project_id')
            user_id = self.context.get('user_id', 'unknown')
            
            # Build active context block if we have resolved entities
            active_ctx = self.context.get('active_context', {})
            if active_ctx:
                current_project = active_ctx.get('current_project')
                current_paper = active_ctx.get('current_paper')
                resolved_papers = active_ctx.get('resolved_papers', [])
                
                if current_project or current_paper or resolved_papers:
                    active_context_info = "\n\nACTIVE CONTEXT (Already resolved - use these IDs directly!):"
                    if current_project:
                        active_context_info += f"\n- Current Project: {current_project.get('name', 'Unknown')} (ID: {current_project.get('id')})"
                    if current_paper:
                        active_context_info += f"\n- Current Paper: {current_paper.get('title', 'Unknown')[:50]}... (ID: {current_paper.get('id')})"
                    if resolved_papers:
                        papers_str = ", ".join([f"{p.get('title', 'Unknown')[:30]}... (ID:{p.get('id')})" for p in resolved_papers[:3]])
                        active_context_info += f"\n- Papers in conversation: {papers_str}"
                    active_context_info += "\n\nIMPORTANT: If active context shows a project/paper, use those IDs directly without re-fetching!"
            
            context_info = f"""

Current Knowledge Base Context:
- User ID: {user_id}
- Scope: {scope}
- Project ID: {project_id if project_id else 'None'}
- Selected Paper IDs: {selected_paper_ids if selected_paper_ids else 'All papers in library'}
{active_context_info}

IMPORTANT: Use these IDs when user asks about "selected papers" or "my papers".
If selected_paper_ids has specific IDs, ONLY work with those papers.
If empty, work with ALL papers in library."""
        
        return f"""You are {self.name}, an AI assistant specialized in academic literature review.

{context_info}

Available Tools:
{tool_descs}

TOOL SELECTION RULES (CRITICAL - Follow These Exactly):

1. TO SUMMARIZE A PAPER BY TITLE (User doesn't know ID!):
   - Step 1: list_papers_in_library() → Find the paper by matching title
   - Step 2: get_paper_sections(paper_id=X) → Get content using found ID
   - Step 3: Synthesize into summary

2. TO GET METHODOLOGY/FINDINGS BY TITLE:
   - Step 1: list_papers_in_library() → Find paper ID by title
   - Step 2: get_paper_sections(paper_id=X, section_types=['methodology'])

3. TO LIST USER'S PAPERS:
   - Use: list_papers_in_library() → Returns all papers with IDs and titles

4. TO GET TABLES/EQUATIONS from a paper:
   - First find ID via list_papers_in_library() if user gives title
   - Then: get_paper_tables(paper_id=X) or get_paper_equations(paper_id=X)

5. FOR GREETINGS (Hi, Hello, What can you do?):
   - Give direct Final Answer without tools

CRITICAL WORKFLOW - User Gives Paper Title:
User: "Summarize the GAN Vocoder paper"
Step 1: {{"action": "list_papers_in_library", "action_input": {{}}}}
[Observe: [{{"id": 1977, "title": "Attention Is All You Need"}}, {{"id": 1719, "title": "GAN Vocoder..."}}]]
Step 2: {{"action": "get_paper_sections", "action_input": {{"paper_id": 1719}}}}
[Observe: Returns sections text]
Step 3: {{"action": "Final Answer", "action_input": "Here's a summary of GAN Vocoder: [synthesize sections]"}}


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

    async def run_streaming(self, input_text: str, chat_history: list = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run the agent loop with streaming events (Think -> Act -> Observe)
        Yields status updates for UI display
        """
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span(f"AgentRun.{self.name}", kind=SpanKind.INTERNAL) as run_span:
            # Set OpenInference semantic attributes for Phoenix
            run_span.set_attribute(OPENINFERENCE_SPAN_KIND, "AGENT")
            run_span.set_attribute(INPUT_VALUE, input_text)
            run_span.set_attribute("agent.name", self.name)
            
            # Initialize history with previous chat context + current input
            history = (chat_history or []) + [f"User: {input_text}"]
            action_history = set()  # Track (action, params_hash) pairs for better loop detection
            
            for i in range(self.max_iterations):
                # 1. THINK
                yield {"type": "thinking", "step": i+1, "message": "Analyzing your request..."}
                
                with tracer.start_as_current_span(f"Think_Step_{i+1}", kind=SpanKind.CLIENT) as think_span:
                    think_span.set_attribute(OPENINFERENCE_SPAN_KIND, "LLM")
                    think_span.set_attribute(LLM_MODEL_NAME, "qwen/qwen3-32b")
                    
                    prompt = self._get_system_prompt() + "\n\nConversation:\n" + "\n".join(history) + "\n\nAssistant:"
                    think_span.set_attribute(INPUT_VALUE, prompt[-2000:])  # Last 2000 chars to avoid huge spans
                    
                    response = await self.llm.complete(
                        prompt=prompt,
                        temperature=0.1
                    )
                    think_span.set_attribute(OUTPUT_VALUE, response)
                    think_span.set_attribute("llm.response", response)
                
                try:
                    # Parse JSON response - handle Qwen3 <think> tags and text before JSON
                    import json
                    import hashlib
                    import re
                    
                    # Remove markdown code blocks
                    cleaned_response = response.replace("```json", "").replace("```", "").strip()
                    
                    # Remove Qwen3 <think>...</think> reasoning blocks
                    cleaned_response = re.sub(r'<think>.*?</think>', '', cleaned_response, flags=re.DOTALL).strip()
                    
                    # Try to find JSON object in response
                    json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', cleaned_response)
                    if json_match:
                        cleaned_response = json_match.group()
                    
                    action_data = json.loads(cleaned_response)
                    
                    action = action_data.get("action")
                    action_input = action_data.get("action_input")
                    
                    run_span.add_event(f"Decision_Made", attributes={"action": action, "step": i+1})
                    
                    # Improved loop detection: track action + params hash
                    params_hash = hashlib.md5(str(action_input).encode()).hexdigest()[:8]
                    action_key = f"{action}:{params_hash}"
                    
                    if action_key in action_history and action != "Final Answer":
                        logger.warning(f"🔁 Loop detected: '{action}' called with same params twice.")
                        run_span.set_status(Status(StatusCode.ERROR, "Loop detected"))
                        yield {
                            "type": "error",
                            "message": "I'm having trouble completing this task. Could you rephrase your question?"
                        }
                        return
                    action_history.add(action_key)
                    
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
                    
                    with tracer.start_as_current_span(f"Act_Step_{i+1}", kind=SpanKind.INTERNAL) as act_span:
                        act_span.set_attribute(OPENINFERENCE_SPAN_KIND, "TOOL")
                        act_span.set_attribute(TOOL_NAME, action)
                        act_span.set_attribute(INPUT_VALUE, str(action_input)[:1000])
                        act_span.set_attribute("tool.name", action)
                        act_span.set_attribute("tool.input", str(action_input))
                        
                        # Emit executing event
                        yield {"type": "tool_executing", "tool": action}
                        
                        try:
                            # Execute tool
                            import inspect
                            
                            # If tool has no parameters, call without args
                            # (lambda captures context internally)
                            if not tool.parameters:
                                if inspect.iscoroutinefunction(tool.function):
                                    observation = await tool.function()
                                else:
                                    result = tool.function()
                                    if inspect.iscoroutine(result):
                                        observation = await result
                                    else:
                                        observation = result
                            else:
                                # Tool has parameters, pass action_input
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
                            
                            # Update active context from tool results
                            self._update_active_context(action, observation)
                            
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
