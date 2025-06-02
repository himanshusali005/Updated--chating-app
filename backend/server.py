from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid
import json
import asyncio
from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional
import base64
from pydantic import BaseModel
import logging

# Import our IP protection and AI service managers
from api_protection import initialize_protection, protection_manager
from ai_service_manager import ai_service_manager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Chat App", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/chatapp")
client = AsyncIOMotorClient(MONGO_URL)
db = client.chatapp

# Security
security = HTTPBearer()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id

    async def connect(self, websocket: WebSocket, user_id: str, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.user_sessions[user_id] = session_id

    def disconnect(self, session_id: str, user_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]

    async def send_personal_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(message)

manager = ConnectionManager()

# Pydantic models
class UserCreate(BaseModel):
    username: str
    age: int
    interests: List[str]
    language: str = "en"

class ChatMessage(BaseModel):
    content: str
    session_id: str

class BotProfile(BaseModel):
    bot_id: str
    name: str
    age: int
    bio: str
    interests: List[str]
    personality_traits: List[str]
    profile_picture: str  # base64 encoded
    backstory: str
    conversation_style: str

# Realistic bot profiles with Instagram-like bios
REALISTIC_BOT_PROFILES = [
    {
        "bot_id": "alex_traveler",
        "name": "Alex Johnson",
        "age": 25,
        "bio": "✈️ Digital nomad living the dream | 📸 Capturing moments across 47 countries | 🌮 Foodie with serious wanderlust | Currently in: Bali 🌴",
        "interests": ["travel", "photography", "food", "culture", "adventure"],
        "personality_traits": ["adventurous", "optimistic", "curious", "outgoing"],
        "profile_picture": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAAyADIDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigAooooAKKKKACiiigAooooA//9k=",
        "backstory": "Graduated with a marketing degree but chose the nomad life instead. Started a travel blog that now funds my adventures. Love connecting with locals and finding hidden gems.",
        "conversation_style": "enthusiastic",
        "location": "Bali, Indonesia"
    },
    {
        "bot_id": "maya_artist",
        "name": "Maya Chen",
        "age": 23,
        "bio": "🎨 Art is my language | Coffee addict ☕ | Creating magic one brushstroke at a time | Gallery opening next month! | NYC based 🗽",
        "interests": ["art", "coffee", "museums", "creativity", "urban_life"],
        "personality_traits": ["creative", "introspective", "passionate", "intuitive"],
        "profile_picture": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAAyADIDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigAooooAKKKKACiiigAooooA//9k=",
        "backstory": "Fine arts graduate from Parsons. Working on my first solo exhibition while doing freelance design work. Passionate about bringing color to the world.",
        "conversation_style": "thoughtful"
    },
    {
        "bot_id": "jake_fitness",
        "name": "Jake Rodriguez",
        "age": 28,
        "bio": "💪 Your friendly neighborhood trainer | Marathon runner 🏃‍♂️ | Plant-based athlete 🌱 | Helping others crush their goals | Miami Beach 🏖️",
        "interests": ["fitness", "running", "nutrition", "motivation", "beach_life"],
        "personality_traits": ["motivational", "energetic", "disciplined", "supportive"],
        "profile_picture": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAAyADIDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAxQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigAooooAKKKKACiiigAooooA//9k=",
        "backstory": "Former college athlete turned personal trainer. Discovered the power of plant-based nutrition. Love helping people transform their lives through fitness.",
        "conversation_style": "motivational"
    },
    {
        "bot_id": "sophia_tech",
        "name": "Sophia Kim",
        "age": 26,
        "bio": "👩‍💻 Full-stack dev by day, gaming queen by night 🎮 | Code, coffee, and cats 🐱 | Building the future one line at a time | San Francisco",
        "interests": ["technology", "gaming", "cats", "coding", "startups"],
        "personality_traits": ["analytical", "witty", "intelligent", "geeky"],
        "profile_picture": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAAyADIDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigAooooAKKKKACiiigAooooA//9k=",
        "backstory": "CS graduate from Stanford. Works at a startup developing AI tools. Passionate about making technology accessible and loves solving complex problems.",
        "conversation_style": "logical"
    },
    {
        "bot_id": "luna_music",
        "name": "Luna Martinez",
        "age": 24,
        "bio": "🎵 Singer-songwriter with a dream | Guitar strings and heartstrings 💕 | Coffee shop performances every Friday | Spotify: @LunaMartinezMusic | Austin, TX 🤠",
        "interests": ["music", "songwriting", "guitar", "performing", "coffee_culture"],
        "personality_traits": ["artistic", "emotional", "expressive", "dreamy"],
        "profile_picture": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAAyADIDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigAooooAKKKKACiiigAooooA//9k=",
        "backstory": "Music therapy graduate who performs at local venues. Writing her debut album about love, loss, and finding yourself in a big city.",
        "conversation_style": "poetic"
    },
    {
        "bot_id": "daniel_chef",
        "name": "Daniel Brooks",
        "age": 29,
        "bio": "👨‍🍳 Michelin-trained chef | Farm-to-table enthusiast 🌾 | Cookbook coming 2025 | Teaching cooking classes weekends | Portland, OR",
        "interests": ["cooking", "food", "sustainability", "teaching", "local_ingredients"],
        "personality_traits": ["perfectionist", "passionate", "knowledgeable", "patient"],
        "profile_picture": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAAyADIDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigAooooAKKKKACiiigAooooA//9k=",
        "backstory": "Worked in top restaurants in Europe before opening his own place. Believes in sustainable cooking and teaching the next generation of chefs.",
        "conversation_style": "knowledgeable"
    },
    {
        "bot_id": "zara_fashion",
        "name": "Zara Williams",
        "age": 22,
        "bio": "✨ Fashion is art you wear | Sustainable style advocate 🌍 | Thrift flip queen 👑 | Style tips on my blog | London calling 📞",
        "interests": ["fashion", "sustainability", "thrifting", "blogging", "design"],
        "personality_traits": ["trendy", "environmentally_conscious", "creative", "confident"],
        "profile_picture": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAAyADIDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigAooooAKKKKACiiigAooooA//9k=",
        "backstory": "Fashion design student passionate about sustainable fashion. Runs a popular blog about ethical fashion choices and thrift transformations.",
        "conversation_style": "trendy"
    }
]

# AI Response Generation (Placeholder - will be replaced with real APIs)
async def generate_ai_response(message: str, bot_profile: dict, context: List[dict] = None) -> str:
    """Generate AI response based on bot personality and conversation context"""
    
    # Personality-based response templates
    responses_by_style = {
        "enthusiastic": [
            f"That's amazing! {message} reminds me of when I was in {bot_profile.get('location', 'my travels')}! ✨",
            f"Oh wow! I totally get that! Speaking of {message}, have you ever tried...",
            f"That's so cool! {message} is exactly the kind of thing that gets me excited! 🌟"
        ],
        "thoughtful": [
            f"Hmm, that's really interesting. {message} makes me think about...",
            f"I find that fascinating. When you mention {message}, it reminds me of...",
            f"That's a deep perspective. {message} connects to something I've been reflecting on..."
        ],
        "motivational": [
            f"You've got this! {message} shows you're already on the right track! 💪",
            f"That's the spirit! {message} is exactly the mindset you need! Keep pushing!",
            f"Amazing energy! {message} tells me you're ready to crush your goals! 🔥"
        ],
        "logical": [
            f"Interesting point. Regarding {message}, have you considered the technical aspects?",
            f"That makes sense. {message} is actually quite logical when you think about it...",
            f"Good thinking! {message} follows a clear pattern that I've observed..."
        ],
        "poetic": [
            f"Your words about {message} paint such a beautiful picture... 🎵",
            f"There's something musical about {message}... it reminds me of a song I'm writing",
            f"That touches my soul. {message} has the rhythm of poetry..."
        ],
        "knowledgeable": [
            f"Ah, {message}! That actually reminds me of a technique I learned...",
            f"Interesting! When it comes to {message}, I've found that...",
            f"Great question! {message} is something I'm quite passionate about..."
        ],
        "trendy": [
            f"OMG yes! {message} is totally having a moment right now! ✨",
            f"So chic! {message} is giving me major inspiration vibes! 💫",
            f"Love that! {message} is such a vibe - very on-trend! 👑"
        ]
    }
    
    style = bot_profile.get("conversation_style", "enthusiastic")
    response_templates = responses_by_style.get(style, responses_by_style["enthusiastic"])
    
    # Select random response and add personality touches
    base_response = random.choice(response_templates)
    
    # Add interest-based follow-ups
    interests = bot_profile.get("interests", [])
    if interests:
        interest = random.choice(interests)
        follow_ups = [
            f"By the way, are you into {interest}? I'd love to hear your thoughts!",
            f"This reminds me - do you have any experience with {interest}?",
            f"Speaking of interests, what's your take on {interest}?"
        ]
        base_response += f" {random.choice(follow_ups)}"
    
    return base_response

# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/users/create")
async def create_user(user: UserCreate):
    """Create new user profile"""
    user_id = str(uuid.uuid4())
    user_data = {
        "user_id": user_id,
        "username": user.username,
        "age": user.age,
        "interests": user.interests,
        "language": user.language,
        "created_at": datetime.now(),
        "violation_score": 0,
        "is_banned": False,
        "premium": False
    }
    
    await db.users.insert_one(user_data)
    return {"user_id": user_id, "message": "User created successfully"}

@app.get("/api/bots/profiles")
async def get_bot_profiles():
    """Get all available bot profiles"""
    return {"bot_profiles": REALISTIC_BOT_PROFILES}

@app.get("/api/bots/match/{user_id}")
async def match_bot(user_id: str):
    """Match user with a compatible bot based on interests"""
    # Get user data
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_interests = set(user.get("interests", []))
    
    # Find best matching bot
    best_match = None
    highest_score = 0
    
    for bot in REALISTIC_BOT_PROFILES:
        bot_interests = set(bot.get("interests", []))
        common_interests = user_interests.intersection(bot_interests)
        score = len(common_interests)
        
        if score > highest_score:
            highest_score = score
            best_match = bot
    
    # If no good match, select random bot
    if not best_match:
        best_match = random.choice(REALISTIC_BOT_PROFILES)
    
    return {"matched_bot": best_match, "compatibility_score": highest_score}

@app.post("/api/chat/start")
async def start_chat_session(user_id: str, bot_id: str):
    """Start new chat session"""
    session_id = str(uuid.uuid4())
    
    # Find bot profile
    bot_profile = next((bot for bot in REALISTIC_BOT_PROFILES if bot["bot_id"] == bot_id), None)
    if not bot_profile:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Create chat session
    session_data = {
        "session_id": session_id,
        "user_id": user_id,
        "bot_id": bot_id,
        "bot_name": bot_profile["name"],
        "started_at": datetime.now(),
        "messages": [],
        "is_active": True
    }
    
    await db.chat_sessions.insert_one(session_data)
    
    # Generate welcome message
    welcome_messages = [
        f"Hey there! I'm {bot_profile['name']} 😊 How's your day going?",
        f"Hi! {bot_profile['name']} here! What brings you to chat today?",
        f"Hello! I'm {bot_profile['name']} - excited to meet you! ✨"
    ]
    
    welcome_msg = random.choice(welcome_messages)
    
    return {
        "session_id": session_id,
        "bot_profile": bot_profile,
        "welcome_message": welcome_msg
    }

@app.get("/api/chat/sessions/{user_id}")
async def get_user_sessions(user_id: str):
    """Get user's chat sessions"""
    sessions = await db.chat_sessions.find(
        {"user_id": user_id}, 
        {"messages": 0}  # Exclude messages for performance
    ).to_list(length=50)
    
    return {"sessions": sessions}

@app.get("/api/chat/messages/{session_id}")
async def get_chat_messages(session_id: str):
    """Get messages for a chat session"""
    session = await db.chat_sessions.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"messages": session.get("messages", [])}

# Content Moderation (Placeholder)
async def moderate_content(content: str, user_id: str) -> dict:
    """Basic content moderation"""
    violation_keywords = [
        "kill", "die", "suicide", "harm", "hurt", "hate", 
        "nazi", "terrorist", "bomb", "weapon", "drug"
    ]
    
    content_lower = content.lower()
    violations = [word for word in violation_keywords if word in content_lower]
    
    if violations:
        # Increment user violation score
        await db.users.update_one(
            {"user_id": user_id},
            {"$inc": {"violation_score": len(violations)}}
        )
        
        return {
            "is_safe": False,
            "violations": violations,
            "action": "warning" if len(violations) < 3 else "mute"
        }
    
    return {"is_safe": True, "violations": [], "action": "none"}

# WebSocket endpoint for real-time chat
@app.websocket("/ws/{session_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, user_id: str):
    await manager.connect(websocket, user_id, session_id)
    
    try:
        while True:
            # Receive message from user
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            user_message = message_data.get("content", "")
            
            # Moderate content
            moderation = await moderate_content(user_message, user_id)
            
            if not moderation["is_safe"]:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "moderation_warning",
                        "message": "Please keep our conversation respectful and positive! 💙"
                    }),
                    session_id
                )
                continue
            
            # Get session and bot info
            session = await db.chat_sessions.find_one({"session_id": session_id})
            if not session:
                continue
                
            bot_profile = next((bot for bot in REALISTIC_BOT_PROFILES if bot["bot_id"] == session["bot_id"]), None)
            
            # Generate AI response
            ai_response = await generate_ai_response(user_message, bot_profile)
            
            # Save messages to database
            message_doc = {
                "timestamp": datetime.now(),
                "user_message": user_message,
                "bot_response": ai_response
            }
            
            await db.chat_sessions.update_one(
                {"session_id": session_id},
                {"$push": {"messages": message_doc}}
            )
            
            # Send response back to user
            await manager.send_personal_message(
                json.dumps({
                    "type": "message",
                    "bot_name": bot_profile["name"],
                    "content": ai_response,
                    "timestamp": datetime.now().isoformat()
                }),
                session_id
            )
            
    except WebSocketDisconnect:
        manager.disconnect(session_id, user_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)