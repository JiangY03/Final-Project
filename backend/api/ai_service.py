"""
AI Service Module - Handles AI model interactions
"""
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class AIService:
    """AI service for handling chat interactions with Ollama"""
    
    def __init__(self):
        self.model_name = settings.AI_MODEL_NAME
        self.base_url = settings.OLLAMA_BASE_URL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.temperature = settings.AI_TEMPERATURE
    
    def generate_response(self, message, context=None):
        """
        Generate AI response using Ollama
        
        Args:
            message (str): User message
            context (list): Previous conversation context
            
        Returns:
            dict: AI response with message and metadata
        """
        try:
            # Build conversation context
            messages = []
            
            # Add system prompt for mental health support
            system_prompt = """You are a supportive mental health assistant. You provide empathetic, 
            non-judgmental responses to help users with their mental wellbeing. You should:
            - Be warm, understanding, and supportive
            - Encourage healthy coping strategies
            - Suggest professional help when appropriate
            - Keep responses concise but helpful
            - Avoid giving medical advice or diagnoses"""
            
            messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation context if available
            if context:
                for msg in context[-5:]:  # Keep last 5 messages for context
                    messages.append(msg)
            
            # Add current user message
            messages.append({"role": "user", "content": message})
            
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
            }
            
            # Make request to Ollama
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_message = result.get('message', {}).get('content', '')
                
                logger.info(f"AI response generated successfully for message: {message[:50]}...")
                
                return {
                    'success': True,
                    'message': ai_message,
                    'model': self.model_name
                }
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'message': 'I apologize, but I\'m having trouble responding right now. Please try again later.',
                    'error': f"API error: {response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            logger.error("Ollama API timeout")
            return {
                'success': False,
                'message': 'I apologize, but I\'m taking too long to respond. Please try again.',
                'error': 'timeout'
            }
        except requests.exceptions.ConnectionError:
            logger.error("Ollama API connection error")
            return {
                'success': False,
                'message': 'I apologize, but I\'m having trouble connecting. Please make sure the AI service is running.',
                'error': 'connection_error'
            }
        except Exception as e:
            logger.error(f"Unexpected error in AI service: {str(e)}")
            return {
                'success': False,
                'message': 'I apologize, but something went wrong. Please try again.',
                'error': str(e)
            }
    
    def is_available(self):
        """
        Check if AI service is available
        
        Returns:
            bool: True if service is available, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

# Global AI service instance
ai_service = AIService()
