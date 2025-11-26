"""
Analytics Engine for ROOMie
Generates insights and statistics from emotion/conversation data
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from conversation_memory import memory
from logger import setup_logger
import json

logger = setup_logger("analytics")

class AnalyticsEngine:
    """Generate analytics and insights from user data"""
    
    async def get_emotion_summary(self, user_id: int, days: int = 7) -> Dict:
        """Get emotion summary for the last N days"""
        try:
            # Get emotion history for specific user
            emotions = await memory.get_emotion_history(user_id, hours=days * 24)
            
            if not emotions:
                return {
                    "total_records": 0,
                    "dominant_emotion": "neutral",
                    "emotion_distribution": {},
                    "average_confidence": 0.0,
                    "mood_score": 50
                }
            
            # Calculate distribution
            emotion_counts = {}
            total_confidence = 0
            
            for record in emotions:
                emotion = record['emotion']
                confidence = record.get('confidence', 0)
                
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                total_confidence += confidence
            
            # Find dominant emotion
            dominant = max(emotion_counts.items(), key=lambda x: x[1])[0]
            
            # Calculate mood score (0-100)
            positive_emotions = ['happy', 'surprise', 'calm']
            negative_emotions = ['sad', 'angry', 'fear']
            
            positive_count = sum(emotion_counts.get(e, 0) for e in positive_emotions)
            negative_count = sum(emotion_counts.get(e, 0) for e in negative_emotions)
            total = len(emotions)
            
            mood_score = int(((positive_count - negative_count) / total + 1) * 50)
            mood_score = max(0, min(100, mood_score))  # Clamp to 0-100
            
            return {
                "total_records": len(emotions),
                "dominant_emotion": dominant,
                "emotion_distribution": emotion_counts,
                "average_confidence": total_confidence / len(emotions) if emotions else 0,
                "mood_score": mood_score,
                "period_days": days
            }
        
        except Exception as e:
            logger.error(f"Error generating emotion summary: {e}")
            return {}
    
    async def get_mood_calendar(self, user_id: int, days: int = 30) -> List[Dict]:
        """Get daily mood data for calendar heatmap"""
        try:
            emotions = await memory.get_emotion_history(user_id, hours=days * 24)
            
            # Group by date
            daily_moods = {}
            
            for record in emotions:
                timestamp = record.get('timestamp', '')
                if not timestamp:
                    continue
                
                date = timestamp.split('T')[0]  # Get date part
                emotion = record['emotion']
                
                if date not in daily_moods:
                    daily_moods[date] = {
                        'date': date,
                        'emotions': {},
                        'count': 0
                    }
                
                daily_moods[date]['emotions'][emotion] = \
                    daily_moods[date]['emotions'].get(emotion, 0) + 1
                daily_moods[date]['count'] += 1
            
            # Calculate dominant emotion and intensity for each day
            calendar_data = []
            for date, data in sorted(daily_moods.items()):
                dominant = max(data['emotions'].items(), key=lambda x: x[1])[0]
                intensity = data['count'] / 10  # Normalize intensity
                intensity = min(1.0, intensity)  # Cap at 1.0
                
                calendar_data.append({
                    'date': date,
                    'dominant_emotion': dominant,
                    'intensity': intensity,
                    'count': data['count'],
                    'emotions': data['emotions']
                })
            
            return calendar_data
        
        except Exception as e:
            logger.error(f"Error generating mood calendar: {e}")
            return []
    
    async def generate_insights(self, user_id: int) -> List[Dict]:
        """Generate AI-powered insights from user data"""
        try:
            # Get data for specific user
            summary = await self.get_emotion_summary(user_id, days=7)
            conversations = await memory.get_recent_conversations(user_id, limit=50)
            
            insights = []
            
            # Insight 1: Dominant emotion
            if summary.get('dominant_emotion'):
                dominant = summary['dominant_emotion']
                count = summary['emotion_distribution'].get(dominant, 0)
                total = summary['total_records']
                percentage = int((count / total) * 100) if total > 0 else 0
                
                insights.append({
                    'type': 'dominant_emotion',
                    'title': f'You\'re mostly {dominant} this week',
                    'description': f'{percentage}% of your emotions were {dominant}',
                    'icon': self._get_emotion_emoji(dominant),
                    'severity': 'info'
                })
            
            # Insight 2: Mood score
            mood_score = summary.get('mood_score', 50)
            if mood_score >= 70:
                insights.append({
                    'type': 'positive_trend',
                    'title': 'Great mood this week! 🎉',
                    'description': f'Your mood score is {mood_score}/100. Keep it up!',
                    'icon': '😊',
                    'severity': 'success'
                })
            elif mood_score <= 30:
                insights.append({
                    'type': 'low_mood',
                    'title': 'Tough week detected',
                    'description': f'Your mood score is {mood_score}/100. Want to talk about it?',
                    'icon': '💙',
                    'severity': 'warning'
                })
            
            # Insight 3: Conversation count
            if len(conversations) > 20:
                insights.append({
                    'type': 'engagement',
                    'title': 'You\'re very engaged!',
                    'description': f'{len(conversations)} conversations this week. ROOMie loves chatting with you!',
                    'icon': '💬',
                    'severity': 'info'
                })
            
            # Insight 4: Emotion variety
            variety = len(summary.get('emotion_distribution', {}))
            if variety >= 5:
                insights.append({
                    'type': 'emotional_range',
                    'title': 'Wide emotional range',
                    'description': f'You\'ve experienced {variety} different emotions. That\'s healthy!',
                    'icon': '🌈',
                    'severity': 'info'
                })
            
            return insights
        
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []
    
    async def get_emotion_trends(self, user_id: int, days: int = 7) -> List[Dict]:
        """Get emotion trends over time"""
        try:
            emotions = await memory.get_emotion_history(user_id, hours=days * 24)
            
            # Group by hour
            hourly_data = {}
            
            for record in emotions:
                timestamp = record.get('timestamp', '')
                if not timestamp:
                    continue
                
                # Parse timestamp and get hour
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                hour_key = dt.strftime('%Y-%m-%d %H:00')
                
                if hour_key not in hourly_data:
                    hourly_data[hour_key] = {
                        'timestamp': hour_key,
                        'emotions': {},
                        'count': 0
                    }
                
                emotion = record['emotion']
                hourly_data[hour_key]['emotions'][emotion] = \
                    hourly_data[hour_key]['emotions'].get(emotion, 0) + 1
                hourly_data[hour_key]['count'] += 1
            
            # Convert to list and calculate scores
            trends = []
            for hour, data in sorted(hourly_data.items()):
                # Calculate positivity score
                positive = data['emotions'].get('happy', 0) + data['emotions'].get('surprise', 0)
                negative = data['emotions'].get('sad', 0) + data['emotions'].get('angry', 0)
                total = data['count']
                
                score = int(((positive - negative) / total + 1) * 50) if total > 0 else 50
                
                trends.append({
                    'timestamp': hour,
                    'mood_score': score,
                    'count': total,
                    'emotions': data['emotions']
                })
            
            return trends
        
        except Exception as e:
            logger.error(f"Error generating trends: {e}")
            return []
    
    def _get_emotion_emoji(self, emotion: str) -> str:
        """Get emoji for emotion"""
        emoji_map = {
            'happy': '😊',
            'sad': '😢',
            'angry': '😠',
            'fear': '😨',
            'surprise': '😲',
            'disgust': '😖',
            'neutral': '😐',
            'calm': '😌'
        }
        return emoji_map.get(emotion, '😐')

# Global instance
analytics_engine = AnalyticsEngine()
