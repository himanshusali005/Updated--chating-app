import os
import asyncio
import logging
from typing import List, Dict, Optional, Any
import random
import json
from api_protection import make_protected_api_call, protection_manager

logger = logging.getLogger(__name__)

class AIServiceManager:
    """
    Advanced AI service manager with IP protection, failover, and multiple API support
    """
    
    def __init__(self):
        # API Keys (load from environment)
        self.api_keys = {
            'gemini': self._load_api_keys('GEMINI_API_KEY'),
            'deepinfra': self._load_api_keys('DEEPINFRA_API_KEY'),
            'huggingface': self._load_api_keys('HUGGINGFACE_API_KEY'),
            'openai': self._load_api_keys('OPENAI_API_KEY')
        }
        
        # API Endpoints
        self.endpoints = {
            'gemini': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
            'deepinfra': 'https://api.deepinfra.com/v1/inference/meta-llama/Llama-2-70b-chat-hf',
            'huggingface': 'https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta',
            'openai': 'https://api.openai.com/v1/chat/completions'
        }
        
        # Service priority (primary -> fallback)
        self.service_priority = ['gemini', 'deepinfra', 'huggingface', 'openai']
        
        # Current API key rotation index for each service
        self.key_rotation_index = {service: 0 for service in self.service_priority}
        
        # Failed services tracking
        self.failed_services = set()
        self.service_retry_times = {}
        
    def _load_api_keys(self, env_var_base: str) -> List[str]:
        """Load multiple API keys from environment variables"""
        keys = []
        
        # Try to load multiple keys (KEY_1, KEY_2, etc.)
        for i in range(1, 6):  # Support up to 5 keys per service
            key = os.getenv(f"{env_var_base}_{i}")
            if key:
                keys.append(key.strip())
        
        # Also try the base key name
        base_key = os.getenv(env_var_base)
        if base_key and base_key not in keys:
            keys.append(base_key.strip())
        
        return [key for key in keys if key]  # Remove empty keys
    
    def _get_next_api_key(self, service: str) -> Optional[str]:
        """Get next API key for rotation"""
        keys = self.api_keys.get(service, [])
        if not keys:
            return None
        
        current_index = self.key_rotation_index[service]
        key = keys[current_index]
        
        # Rotate to next key
        self.key_rotation_index[service] = (current_index + 1) % len(keys)
        
        return key
    
    async def _make_gemini_request(self, prompt: str, context: List[Dict] = None) -> Optional[str]:
        """Make request to Gemini Pro API with protection"""
        api_key = self._get_next_api_key('gemini')
        if not api_key:
            logger.error("No Gemini API keys available")
            return None
        
        url = f"{self.endpoints['gemini']}?key={api_key}"
        
        # Prepare context for Gemini
        contents = []
        if context:
            for msg in context[-10:]:  # Last 10 messages for context
                contents.append({
                    "parts": [{"text": msg.get("content", "")}]
                })
        
        contents.append({
            "parts": [{"text": prompt}]
        })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 256,
                "stopSequences": []
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = await make_protected_api_call(
                "POST", url, "gemini", api_key,
                json=payload, headers=headers
            )
            
            if response and "candidates" in response:
                if len(response["candidates"]) > 0:
                    content = response["candidates"][0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            
            logger.warning("Gemini API returned unexpected response format")
            return None
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return None
    
    async def _make_deepinfra_request(self, prompt: str, context: List[Dict] = None) -> Optional[str]:
        """Make request to DeepInfra API with protection"""
        api_key = self._get_next_api_key('deepinfra')
        if not api_key:
            logger.error("No DeepInfra API keys available")
            return None
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Prepare conversation context
        input_text = ""
        if context:
            for msg in context[-8:]:  # Last 8 messages
                role = "Human" if msg.get("type") == "user" else "Assistant"
                input_text += f"{role}: {msg.get('content', '')}\n"
        
        input_text += f"Human: {prompt}\nAssistant:"
        
        payload = {
            "input": input_text,
            "max_tokens": 256,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        try:
            response = await make_protected_api_call(
                "POST", self.endpoints['deepinfra'], "deepinfra", api_key,
                json=payload, headers=headers
            )
            
            if response and "results" in response:
                if len(response["results"]) > 0:
                    return response["results"][0].get("generated_text", "").strip()
            
            logger.warning("DeepInfra API returned unexpected response format")
            return None
            
        except Exception as e:
            logger.error(f"DeepInfra API error: {str(e)}")
            return None
    
    async def _make_huggingface_request(self, prompt: str, context: List[Dict] = None) -> Optional[str]:
        """Make request to Hugging Face API with protection"""
        api_key = self._get_next_api_key('huggingface')
        if not api_key:
            logger.error("No Hugging Face API keys available")
            return None
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare conversation for Zephyr format
        conversation = ""
        if context:
            for msg in context[-6:]:  # Last 6 messages
                role = "user" if msg.get("type") == "user" else "assistant"
                conversation += f"<|{role}|>\n{msg.get('content', '')}\n"
        
        conversation += f"<|user|>\n{prompt}\n<|assistant|>\n"
        
        payload = {
            "inputs": conversation,
            "parameters": {
                "max_new_tokens": 256,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True
            }
        }
        
        try:
            response = await make_protected_api_call(
                "POST", self.endpoints['huggingface'], "huggingface", api_key,
                json=payload, headers=headers
            )
            
            if response and isinstance(response, list) and len(response) > 0:
                generated_text = response[0].get("generated_text", "")
                # Extract only the assistant's response
                if "<|assistant|>" in generated_text:
                    assistant_response = generated_text.split("<|assistant|>")[-1].strip()
                    return assistant_response
            
            logger.warning("Hugging Face API returned unexpected response format")
            return None
            
        except Exception as e:
            logger.error(f"Hugging Face API error: {str(e)}")
            return None
    
    async def _make_openai_request(self, prompt: str, context: List[Dict] = None) -> Optional[str]:
        """Make request to OpenAI API with protection"""
        api_key = self._get_next_api_key('openai')
        if not api_key:
            logger.error("No OpenAI API keys available")
            return None
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare conversation context
        messages = [{"role": "system", "content": "You are a helpful, friendly AI assistant."}]
        
        if context:
            for msg in context[-10:]:  # Last 10 messages
                role = "user" if msg.get("type") == "user" else "assistant"
                messages.append({"role": role, "content": msg.get("content", "")})
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": 256,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        try:
            response = await make_protected_api_call(
                "POST", self.endpoints['openai'], "openai", api_key,
                json=payload, headers=headers
            )
            
            if response and "choices" in response:
                if len(response["choices"]) > 0:
                    message = response["choices"][0].get("message", {})
                    return message.get("content", "").strip()
            
            logger.warning("OpenAI API returned unexpected response format")
            return None
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return None
    
    async def generate_response(self, prompt: str, bot_profile: Dict, context: List[Dict] = None) -> str:
        """
        Generate AI response with failover system and IP protection
        """
        
        # Add personality context to prompt
        personality_prompt = f"""
        You are {bot_profile.get('name', 'Assistant')}, a {bot_profile.get('age', 25)}-year-old with the following personality:
        
        Bio: {bot_profile.get('bio', '')}
        Personality traits: {', '.join(bot_profile.get('personality_traits', []))}
        Interests: {', '.join(bot_profile.get('interests', []))}
        Conversation style: {bot_profile.get('conversation_style', 'friendly')}
        
        Respond naturally as this character would, matching their personality and interests. Keep responses conversational and engaging.
        Don't mention that you're an AI or bot.
        
        User message: {prompt}
        """
        
        # Try each service in priority order
        for service in self.service_priority:
            if service in self.failed_services:
                continue
            
            if not self.api_keys.get(service):
                logger.warning(f"No API keys configured for {service}")
                continue
            
            logger.info(f"Attempting to generate response using {service}")
            
            try:
                if service == 'gemini':
                    response = await self._make_gemini_request(personality_prompt, context)
                elif service == 'deepinfra':
                    response = await self._make_deepinfra_request(personality_prompt, context)
                elif service == 'huggingface':
                    response = await self._make_huggingface_request(personality_prompt, context)
                elif service == 'openai':
                    response = await self._make_openai_request(personality_prompt, context)
                else:
                    continue
                
                if response and response.strip():
                    logger.info(f"Successfully generated response using {service}")
                    return response.strip()
                
            except Exception as e:
                logger.error(f"Service {service} failed: {str(e)}")
                self.failed_services.add(service)
                continue
        
        logger.warning("All AI services failed, using fallback response")
        return await self._generate_fallback_response(prompt, bot_profile, context)
    
    async def _generate_fallback_response(self, prompt: str, bot_profile: Dict, context: List[Dict] = None) -> str:
        """Generate fallback response when all APIs fail"""
        style = bot_profile.get("conversation_style", "friendly")
        name = bot_profile.get("name", "Assistant")
        
        fallback_responses = {
            "enthusiastic": [
                f"That's so interesting! I'd love to hear more about that! ✨",
                f"Wow, that's amazing! Tell me more! 🌟",
                f"That sounds incredible! I'm really curious about your thoughts on this! 💫"
            ],
            "thoughtful": [
                f"That's a fascinating perspective. I've been thinking about something similar...",
                f"Hmm, that's really thought-provoking. It makes me reflect on...",
                f"Interesting point. That connects to something I've been pondering..."
            ],
            "motivational": [
                f"You've got this! That's exactly the kind of thinking that leads to success! 💪",
                f"I love your energy! Keep that momentum going! 🔥",
                f"That's the spirit! You're on the right track! ⚡"
            ],
            "logical": [
                f"That's a logical approach. Have you considered the broader implications?",
                f"Interesting analysis. Let's think through this systematically...",
                f"Good reasoning. That follows a clear logical pattern..."
            ],
            "poetic": [
                f"Your words paint such a beautiful picture... 🎵",
                f"There's something lyrical about what you're saying... ✨",
                f"That touches something deep... like a melody in my mind... 🎶"
            ],
            "knowledgeable": [
                f"That's a great topic! Based on my experience...",
                f"Ah, that reminds me of something I learned recently...",
                f"Interesting! That connects to several concepts I'm familiar with..."
            ],
            "trendy": [
                f"OMG yes! That's totally having a moment right now! ✨",
                f"So chic! You're definitely onto something trendy there! 💫",
                f"Love that vibe! You've got such great taste! 👑"
            ]
        }
        
        responses = fallback_responses.get(style, fallback_responses["enthusiastic"])
        return random.choice(responses)
    
    def get_service_status(self) -> Dict:
        """Get current status of all AI services"""
        status = {}
        for service in self.service_priority:
            status[service] = {
                "available_keys": len(self.api_keys.get(service, [])),
                "failed": service in self.failed_services,
                "current_key_index": self.key_rotation_index.get(service, 0)
            }
        return status
    
    def reset_failed_services(self):
        """Reset failed services (useful for recovery)"""
        self.failed_services.clear()
        logger.info("Reset all failed services")

# Global AI service manager instance
ai_service_manager = AIServiceManager()