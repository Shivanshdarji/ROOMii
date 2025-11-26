"""
Conversation memory and history management for ROOMie
"""
import aiosqlite
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from logger import setup_logger

logger = setup_logger("conversation_memory")

from werkzeug.security import generate_password_hash, check_password_hash

class ConversationMemory:
    """Manages conversation history and emotion tracking"""
    
    def __init__(self, db_path: str = "roomie_data.db"):
        self.db_path = db_path
        self.conversation_context = []
        self.emotion_history = []
        
    async def initialize(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Check if password_hash column exists (migration)
            async with db.execute("PRAGMA table_info(users)") as cursor:
                columns = [row[1] for row in await cursor.fetchall()]
                if "password_hash" not in columns:
                    logger.info("Migrating users table to include password_hash")
                    await db.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")

            # Conversations table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    emotion TEXT,
                    sentiment TEXT,
                    personality TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            
            # Check if user_id column exists in conversations (migration)
            async with db.execute("PRAGMA table_info(conversations)") as cursor:
                columns = [row[1] for row in await cursor.fetchall()]
                if "user_id" not in columns:
                    logger.info("Migrating conversations table to include user_id")
                    await db.execute("ALTER TABLE conversations ADD COLUMN user_id INTEGER")

            # Emotion history table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS emotion_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    emotion TEXT NOT NULL,
                    confidence REAL,
                    mood_state TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)

            # Check if user_id column exists in emotion_history (migration)
            async with db.execute("PRAGMA table_info(emotion_history)") as cursor:
                columns = [row[1] for row in await cursor.fetchall()]
                if "user_id" not in columns:
                    logger.info("Migrating emotion_history table to include user_id")
                    await db.execute("ALTER TABLE emotion_history ADD COLUMN user_id INTEGER")
            
            # User preferences table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER,
                    key TEXT,
                    value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, key),
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            
            # Emotion calibration table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS emotion_calibration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    emotion TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            
            await db.commit()
            logger.info("Database initialized successfully")

    async def create_user(self, username: str, password: str) -> int:
        """Create a new user with password"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                password_hash = generate_password_hash(password)
                cursor = await db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                    (username, password_hash)
                )
                await db.commit()
                logger.info(f"Created new user: {username}")
                return cursor.lastrowid
            except Exception as e:
                logger.error(f"Error creating user {username}: {e}")
                return None

    async def verify_user(self, username: str, password: str) -> Optional[int]:
        """Verify user credentials and return user ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, password_hash FROM users WHERE username = ?", 
                (username,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    user_id, stored_hash = row
                    # If no password set (legacy user), allow login and maybe prompt to set one?
                    # For now, we'll assume if hash exists we check it.
                    if stored_hash and check_password_hash(stored_hash, password):
                        # Update last seen
                        await db.execute("UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
                        await db.commit()
                        return user_id
                    elif not stored_hash:
                        # Legacy user without password - allow for now or handle migration
                        # Let's just update the password if they provide one? 
                        # No, that's insecure. Let's fail and require a specific migration flow or just fail.
                        # For simplicity in this prototype: if no hash, allow any password and set it?
                        # Let's just return None if verification fails.
                        pass
                return None

    async def get_user_by_username(self, username: str) -> Optional[int]:
        """Get user ID by username (internal use)"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id FROM users WHERE username = ?", (username,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None
    
    async def add_conversation(
        self, 
        user_id: int,
        user_message: str, 
        bot_response: str,
        emotion: str = "neutral",
        sentiment: str = "neutral",
        personality: str = "neutral"
    ):
        """Store a conversation exchange"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO conversations 
                   (user_id, user_message, bot_response, emotion, sentiment, personality)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, user_message, bot_response, emotion, sentiment, personality)
            )
            await db.commit()
        
        # Update in-memory context (per user context management could be added here)
        # For now, we'll just append to the global context but ideally this should be per-user
        # or we fetch from DB when needed.
        self.conversation_context.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        self.conversation_context.append({
            "role": "assistant",
            "content": bot_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last N messages
        if len(self.conversation_context) > 20:
            self.conversation_context = self.conversation_context[-20:]
        
        logger.debug(f"Conversation stored for user {user_id}")
    
    async def add_emotion_record(
        self, 
        user_id: int,
        emotion: str, 
        confidence: float = 0.0,
        mood_state: str = "neutral"
    ):
        """Store emotion detection record"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO emotion_history (user_id, emotion, confidence, mood_state)
                   VALUES (?, ?, ?, ?)""",
                (user_id, emotion, confidence, mood_state)
            )
            await db.commit()
    
    async def get_recent_conversations(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Retrieve recent conversations for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM conversations 
                   WHERE user_id = ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (user_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_emotion_history(self, user_id: int, hours: int = 24) -> List[Dict]:
        """Get emotion history for the last N hours for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM emotion_history 
                   WHERE user_id = ? AND timestamp > datetime('now', '-' || ? || ' hours')
                   ORDER BY timestamp DESC""",
                (user_id, hours)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_context_for_ai(self, user_id: int, max_messages: int = 10) -> List[Dict]:
        """Get conversation context formatted for AI from DB"""
        # Fetch from DB instead of memory to ensure user isolation
        recent = await self.get_recent_conversations(user_id, max_messages)
        # Convert to AI format (reverse order because get_recent returns DESC)
        context = []
        for row in reversed(recent):
            context.append({"role": "user", "content": row["user_message"]})
            context.append({"role": "assistant", "content": row["bot_response"]})
        return context
    
    async def set_preference(self, user_id: int, key: str, value: str):
        """Store user preference"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO user_preferences (user_id, key, value, updated_at)
                   VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
                (user_id, key, value)
            )
            await db.commit()
        logger.info(f"Preference set for user {user_id}: {key} = {value}")
    
    async def get_preference(self, user_id: int, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve user preference"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT value FROM user_preferences WHERE user_id = ? AND key = ?",
                (user_id, key)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else default
    
    async def clear_old_data(self, days: int = 30):
        """Clean up old conversation data"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """DELETE FROM conversations 
                   WHERE timestamp < datetime('now', '-' || ? || ' days')""",
                (days,)
            )
            await db.execute(
                """DELETE FROM emotion_history 
                   WHERE timestamp < datetime('now', '-' || ? || ' days')""",
                (days,)
            )
            await db.commit()
        logger.info(f"Cleaned up data older than {days} days")

    async def clear_user_history(self, user_id: int):
        """Clear all history for a specific user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
            await db.execute("DELETE FROM emotion_history WHERE user_id = ?", (user_id,))
            await db.commit()
        logger.info(f"Cleared history for user {user_id}")

# Global instance
memory = ConversationMemory()
