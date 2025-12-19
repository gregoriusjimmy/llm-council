import asyncio
from ollama import AsyncClient
import time

class CouncilMember:
    def __init__(self, name, model, role_description):
        self.name = name
        self.model = model
        self.role_description = role_description

class CouncilManager:
    def __init__(self):
        self.members = []
        self.chairman = None

    def set_council(self, members, chairman_model="deepseek-r1"):
        """
        members: list of CouncilMember objects
        chairman_model: string, name of the model to act as chairman
        """
        self.members = members
        self.chairman = CouncilMember("Chairman", chairman_model, "You are the Chairman of the LLM Council. Your job is to synthesize the answers from other members into a single, perfect response.")

    async def check_models_availability(self):
        """Checks which requested models are actually available locally."""
        try:
            async with AsyncClient() as client:
                available = await client.list()
                available_names = [m['name'] for m in available['models']]
            
            missing = []
            all_requested = set([m.model for m in self.members] + [self.chairman.model])
            
            # Normalize names (remove :latest if needed or handle exact matches)
            # Simple check
            for req in all_requested:
                # partial match check because 'llama3' might be 'llama3:latest'
                if not any(req in av for av in available_names):
                    missing.append(req)
            
            return missing
        except Exception as e:
            return [f"Error connecting to Ollama: {str(e)}"]

    async def _get_member_response(self, member, prompt, history=None, timeout=120):
        """Gets a response from a single member with timeout."""
        system_prompt = f"You are {member.name}. {member.role_description}"
        
        messages = [{'role': 'system', 'content': system_prompt}]
        if history:
            # Append recent history (last 10 messages to keep context window manageable)
            # Filter out 'system' messages from history if any, stick to user/assistant
            recent_history = history[-10:]
            for msg in recent_history:
                 messages.append({'role': msg['role'], 'content': msg['content']})
        
        messages.append({'role': 'user', 'content': prompt})

        try:
            async with AsyncClient() as client:
                # Use asyncio.wait_for to enforce timeout
                response = await asyncio.wait_for(
                    client.chat(model=member.model, messages=messages),
                    timeout=timeout
                )
                return {
                    "name": member.name,
                    "model": member.model,
                    "content": response['message']['content'],
                    "status": "success"
                }
        except asyncio.TimeoutError:
            return {
                "name": member.name,
                "model": member.model,
                "content": f"Error: Request timed out after {timeout} seconds.",
                "status": "timeout"
            }
        except Exception as e:
            return {
                "name": member.name,
                "model": member.model,
                "content": f"Error: {str(e)}",
                "status": "error"
            }

    async def get_council_responses(self, prompt, history=None):
        """Queries all council members in parallel."""
        # DeepSeek R1 and Thinking models can be slow, giving them more time
        tasks = [self._get_member_response(member, prompt, history, timeout=180) for member in self.members]
        results = await asyncio.gather(*tasks)
        return results

    async def synthesize(self, prompt, council_results, history=None):
        """Chairman synthesizes the results after a critique phase (Supports Streaming)."""
        
        # 1. Prepare Initial Opinions
        context = f"The user asked: '{prompt}'\n\nHere are the initial opinions from the council:\n\n"
        for res in council_results:
            if res['status'] == 'success':
                context += f"--- Opinion of {res['name']} ({res['model']}) ---\n{res['content']}\n\n"
            else:
                 context += f"--- Opinion of {res['name']} ({res['model']}) ---\n[Member failed to respond: {res['content']}]\n\n"
        
        # 2. Critique Phase (Self-Reflection for the Chairman)
        critique_prompt = context + "\n\nCRITICAL ANALYSIS: Identify conflicts, potential errors, and missing perspectives in the council's opinions. What is the strongest argument? What is the weakest?"
        
        # We ask the chairman to critique first (internal monologue)
        critique_response = await self._get_member_response(self.chairman, critique_prompt, history, timeout=180)
        critique_text = critique_response['content'] if critique_response['status'] == 'success' else "Critique failed."

        # 3. Final Synthesis (Streaming)
        final_prompt = f"{context}\n\n--- Chairman's Internal Critique ---\n{critique_text}\n\nBased on the opinions and your critique, provide a comprehensive, best-possible answer. Correct any mistakes. Merge insights into a coherent response."

        # Create message history for final call
        messages = [{'role': 'system', 'content': self.chairman.role_description}]
        if history:
            recent_history = history[-10:]
            for msg in recent_history:
                 messages.append({'role': msg['role'], 'content': msg['content']})
        messages.append({'role': 'user', 'content': final_prompt})

        # Return a generator/async iterator for streaming
        async with AsyncClient() as client:
            stream = await client.chat(model=self.chairman.model, messages=messages, stream=True)
            async for chunk in stream:
                yield chunk

# Default configuration helper
def get_default_council():
    # Updated to High-Performance Models
    return [
        CouncilMember("The Reasoner", "kimi-k2-thinking:cloud", "You are a deep thinker. Break down the user's problem step-by-step."),
        CouncilMember("The Engineer", "minimax-m2:cloud", "You are an engineer. Focus on practical implementation, code, and efficiency."),
        CouncilMember("The Generalist", "deepseek-v3.2:cloud", "You are a balanced assistant. Provide clear, direct answers.")
    ]
