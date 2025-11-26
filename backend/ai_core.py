from openai import OpenAI
from personality import PERSONALITIES, current_persona
import random
from config import Config
from logger import setup_logger
from typing import AsyncGenerator, List, Dict

logger = setup_logger("ai_core")
client = OpenAI(api_key=Config.OPENAI_API_KEY)

def generate_response(
    user_text: str, 
    emotion: str, 
    sentiment: str, 
    history: List[Dict] = None,
    personality: str = None
) -> str:
    """Generate AI response (non-streaming version for compatibility)"""
    if history is None:
        history = []
    
    if personality is None:
        personality = current_persona
        
    persona = PERSONALITIES.get(personality, PERSONALITIES["neutral"])
    
    prompt = f"""
    You are ROOMii, an emotionally intelligent AI roommate and friend.
    Your personality: {personality} — {persona['style']}.
    Speaking style: {persona['prompt_tone']}
    
    The user's detected emotion is {emotion}, and their voice sentiment is {sentiment}.
    Your goal: respond in a friendly, natural, and emotionally aware way.
    Keep your tone conversational, not robotic.
    Never repeat exact phrasing — sound like a genuine friend who listens and cares.
    Keep responses concise (2-3 sentences max) unless the user asks for more detail.
    """

    # Build chat history
    chat_history = [{"role": "system", "content": prompt}]
    
    # Add conversation context
    for msg in history[-Config.CONVERSATION_CONTEXT_LENGTH:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if content:
            chat_history.append({"role": role, "content": content})
    
    # Add current message
    chat_history.append({"role": "user", "content": user_text})

    try:
        response = client.chat.completions.create(
            model=Config.AI_MODEL,
            messages=chat_history,
            temperature=Config.AI_TEMPERATURE,
            max_tokens=Config.AI_MAX_TOKENS
        )
        
        reply = response.choices[0].message.content.strip()
        logger.info(f"AI response generated: {reply[:50]}...")
        return reply
        
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        return "I'm having trouble thinking right now. Can you try again?"


async def generate_response_stream(
    user_text: str,
    emotion: str,
    sentiment: str,
    history: List[Dict] = None,
    personality: str = None
) -> AsyncGenerator[str, None]:
    """Generate AI response with streaming"""
    if history is None:
        history = []
    
    if personality is None:
        personality = current_persona
        
    persona = PERSONALITIES.get(personality, PERSONALITIES["neutral"])
    
    prompt = f"""
    You are ROOMii, an emotionally intelligent AI roommate and friend.
    Your personality: {personality} — {persona['style']}.
    Speaking style: {persona['prompt_tone']}
    
    The user's detected emotion is {emotion}, and their voice sentiment is {sentiment}.
    Your goal: respond in a friendly, natural, and emotionally aware way.
    Keep your tone conversational, not robotic.
    Never repeat exact phrasing — sound like a genuine friend who listens and cares.
    Keep responses concise (2-3 sentences max) unless the user asks for more detail.
    """

    # Build chat history
    chat_history = [{"role": "system", "content": prompt}]
    
    # Add conversation context
    for msg in history[-Config.CONVERSATION_CONTEXT_LENGTH:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if content:
            chat_history.append({"role": role, "content": content})
    
    # Add current message
    chat_history.append({"role": "user", "content": user_text})

    try:
        stream = client.chat.completions.create(
            model=Config.AI_MODEL,
            messages=chat_history,
            temperature=Config.AI_TEMPERATURE,
            max_tokens=Config.AI_MAX_TOKENS,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        logger.error(f"AI streaming error: {e}")
        yield "I'm having trouble thinking right now. Can you try again?"



