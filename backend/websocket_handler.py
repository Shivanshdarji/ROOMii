"""
WebSocket handler for real-time communication with ROOMie frontend
"""
from flask_socketio import SocketIO, emit
from flask import request
import asyncio
from logger import setup_logger
from emotion_detector import get_cached_emotion, BackgroundEmotionMonitor
from ai_core import generate_response
from tts_output import speak_async, cleanup_audio_file
from conversation_memory import memory
from mood_manager import update_mood
from main import choose_personality
from config import Config
import time

logger = setup_logger("websocket")

# Global emotion monitor
emotion_monitor = None

def init_socketio(app):
    """Initialize SocketIO with Flask app"""
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*",
        async_mode='threading',
        logger=True,
        engineio_logger=False
    )
    
    # Store user sessions and processing flags
    user_sessions = {}
    processing_flags = {} # sid -> bool (True = keep processing, False = stop)

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info(f"Client connected: {request.sid}")
        emit('connected', {'message': 'Connected to ROOMii backend'})
        
        # Start background emotion monitoring
        global emotion_monitor
        if emotion_monitor is None:
            emotion_monitor = BackgroundEmotionMonitor(interval=5.0)
            emotion_monitor.start()

    @socketio.on('restore_session')
    def handle_restore_session(data):
        """Handle session restoration from local storage"""
        user_id = data.get('user_id')
        username = data.get('username')
        
        if user_id and username:
            # In a real app, we would verify a token here.
            # For now, we trust the client's stored ID/username match.
            user_sessions[request.sid] = user_id
            logger.info(f"Session restored for user: {username} (ID: {user_id})")
            emit('login_success', {'user_id': user_id, 'username': username})
            
            # Send history immediately
            history = asyncio.run(memory.get_recent_conversations(user_id, 20))
            emit('conversation_history', {'history': history})

    @socketio.on('stop_response')
    def handle_stop_response():
        """Handle request to stop current processing"""
        if request.sid in processing_flags:
            processing_flags[request.sid] = False
            logger.info(f"Stopping processing for session {request.sid}")

    @socketio.on('auth_signup')
    def handle_signup(data):
        """Handle user signup"""
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            emit('auth_error', {'message': 'Username and password required'})
            return
            
        user_id = asyncio.run(memory.create_user(username, password))
        if user_id:
            user_sessions[request.sid] = user_id
            logger.info(f"User signed up: {username} (ID: {user_id})")
            emit('login_success', {'user_id': user_id, 'username': username})
            # Send history immediately
            history = asyncio.run(memory.get_recent_conversations(user_id, 20))
            emit('conversation_history', {'history': history})
        else:
            emit('auth_error', {'message': 'Username already exists'})

    @socketio.on('auth_login')
    def handle_login(data):
        """Handle user login"""
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            emit('auth_error', {'message': 'Username and password required'})
            return

        user_id = asyncio.run(memory.verify_user(username, password))
        if user_id:
            user_sessions[request.sid] = user_id
            logger.info(f"User logged in: {username} (ID: {user_id})")
            emit('login_success', {'user_id': user_id, 'username': username})
            # Send history immediately
            history = asyncio.run(memory.get_recent_conversations(user_id, 20))
            emit('conversation_history', {'history': history})
        else:
            emit('auth_error', {'message': 'Invalid username or password'})

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        if request.sid in user_sessions:
            del user_sessions[request.sid]
        if request.sid in processing_flags:
            del processing_flags[request.sid]
        logger.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('get_emotion')
    def handle_get_emotion():
        """Send current cached emotion"""
        emotion, confidence = get_cached_emotion()
        emit('emotion_update', {
            'emotion': emotion,
            'confidence': float(confidence),
            'timestamp': time.time()
        })
    
    @socketio.on('send_message')
    def handle_message(data):
        """Handle incoming user message"""
        try:
            # Set processing flag to True for this new request
            processing_flags[request.sid] = True
            
            user_message = data.get('message', '').strip()
            if not user_message:
                emit('error', {'message': 'Empty message received'})
                return
            
            user_id = user_sessions.get(request.sid)
            if not user_id:
                emit('error', {'message': 'User not logged in'})
                return

            logger.info(f"Received message from user {user_id}: {user_message}")
            
            # Check cancellation
            if not processing_flags.get(request.sid, True):
                logger.info("Processing cancelled by user")
                return

            # Get current emotion from face
            face_emotion, face_confidence = get_cached_emotion()
            
            # Analyze voice tone from text
            from voice_tone_analyzer import analyze_voice_tone, combine_emotions
            voice_emotion, voice_confidence = analyze_voice_tone(text=user_message)
            
            # Combine face and voice emotions
            emotion, confidence = combine_emotions(
                face_emotion, face_confidence,
                voice_emotion, voice_confidence
            )
            
            logger.info(f"Combined emotion: {emotion} (face: {face_emotion}, voice: {voice_emotion})")
            
            sentiment = "neutral"  # TODO: Add sentiment analysis
            
            mood_state, _ = update_mood(emotion, sentiment)
            combined_mood = mood_state["combined_mood"]
            
            # Choose personality
            persona = choose_personality(combined_mood)
            
            # Get conversation context
            context = asyncio.run(memory.get_context_for_ai(
                user_id, 
                max_messages=Config.CONVERSATION_CONTEXT_LENGTH
            ))
            
            # Check cancellation before expensive generation
            if not processing_flags.get(request.sid, True):
                logger.info("Processing cancelled before generation")
                return

            # Generate AI response
            response_text = generate_response(
                user_message,
                emotion,
                sentiment,
                history=context,
                personality=combined_mood
            )
            
            # Check cancellation before sending
            if not processing_flags.get(request.sid, True):
                logger.info("Processing cancelled before sending response")
                return

            # Send text response immediately
            emit('message_response', {
                'text': response_text,
                'emotion': emotion,
                'mood': combined_mood,
                'personality': persona['name']
            })
            
            # Generate audio in background
            socketio.start_background_task(
                generate_and_send_audio,
                response_text,
                persona['tone'],
                request.sid
            )
            
            # Store conversation (async)
            asyncio.run(memory.add_conversation(
                user_id,
                user_message,
                response_text,
                emotion,
                sentiment,
                combined_mood
            ))
            
            # Store emotion record
            asyncio.run(memory.add_emotion_record(
                user_id,
                emotion,
                confidence,
                combined_mood
            ))
            
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            emit('error', {'message': 'Failed to process message'})
    
    @socketio.on('voice_command')
    def handle_voice_command(data):
        """Handle voice command from user"""
        try:
            from voice_commands import voice_handler
            
            text = data.get('text', '').strip()
            if not text:
                emit('command_response', {
                    'success': False,
                    'message': 'No command text received'
                })
                return
            
            logger.info(f"Processing voice command: {text}")
            
            # Parse command
            command_data = voice_handler.parse_command(text)
            
            # Execute if confidence is high enough
            if command_data['confidence'] >= 0.7:
                result = voice_handler.execute_command(command_data)
                emit('command_response', result)
                logger.info(f"Command executed: {result['action']}")
            else:
                # Not a command, treat as normal message
                emit('command_response', {
                    'success': False,
                    'message': 'Not a recognized command',
                    'is_message': True
                })
        
        except Exception as e:
            logger.error(f"Voice command error: {e}")
            emit('command_response', {
                'success': False,
                'message': 'Failed to process command'
            })
    
    def generate_and_send_audio(text, tone, sid):
        """Background task to generate and send audio"""
        try:
            # Check cancellation before expensive audio generation
            if not processing_flags.get(sid, True):
                logger.info("Audio generation cancelled")
                return

            # Generate audio
            audio_path = asyncio.run(speak_async(text, tone))
            
            # Check cancellation before sending
            if not processing_flags.get(sid, True):
                logger.info("Audio sending cancelled")
                cleanup_audio_file(audio_path)
                return

            if audio_path:
                # Send audio URL
                socketio.emit('audio_ready', {
                    'audio_url': f"/{audio_path}"
                }, room=sid)
                
                # Schedule cleanup
                socketio.sleep(Config.AUDIO_CLEANUP_DELAY)
                cleanup_audio_file(audio_path)
        except Exception as e:
            logger.error(f"Audio generation error: {e}")
    
    @socketio.on('get_conversation_history')
    def handle_get_history(data):
        """Send conversation history"""
        try:
            user_id = user_sessions.get(request.sid)
            if not user_id:
                return
                
            limit = data.get('limit', 20)
            history = asyncio.run(memory.get_recent_conversations(user_id, limit))
            emit('conversation_history', {'history': history})
        except Exception as e:
            logger.error(f"History retrieval error: {e}")
            emit('error', {'message': 'Failed to retrieve history'})
    
    @socketio.on('get_emotion_history')
    def handle_get_emotion_history(data):
        """Send emotion history"""
        try:
            user_id = user_sessions.get(request.sid)
            if not user_id:
                return

            hours = data.get('hours', 24)
            history = asyncio.run(memory.get_emotion_history(user_id, hours))
            emit('emotion_history', {'history': history})
        except Exception as e:
            logger.error(f"Emotion history retrieval error: {e}")
            emit('error', {'message': 'Failed to retrieve emotion history'})

    @socketio.on('clear_history')
    def handle_clear_history():
        """Clear user history"""
        try:
            user_id = user_sessions.get(request.sid)
            if not user_id:
                emit('error', {'message': 'User not logged in'})
                return

            asyncio.run(memory.clear_user_history(user_id))
            emit('history_cleared', {'message': 'Chat history cleared'})
            logger.info(f"History cleared for user {user_id}")
        except Exception as e:
            logger.error(f"History clear error: {e}")
            emit('error', {'message': 'Failed to clear history'})
    
    @socketio.on('get_analytics')
    def handle_get_analytics(data):
        """Send analytics data"""
        try:
            user_id = user_sessions.get(request.sid)
            if not user_id:
                emit('error', {'message': 'User not logged in'})
                return
                
            from analytics import analytics_engine
            
            days = data.get('days', 7)
            
            # Get all analytics data for this user
            summary = asyncio.run(analytics_engine.get_emotion_summary(user_id, days))
            calendar = asyncio.run(analytics_engine.get_mood_calendar(user_id, 30))
            insights = asyncio.run(analytics_engine.generate_insights(user_id))
            trends = asyncio.run(analytics_engine.get_emotion_trends(user_id, days))
            
            emit('analytics_data', {
                'summary': summary,
                'calendar': calendar,
                'insights': insights,
                'trends': trends
            })
            
            logger.info(f"Analytics data sent for user {user_id} ({days} days)")
        except Exception as e:
            logger.error(f"Analytics retrieval error: {e}")
            emit('error', {'message': 'Failed to retrieve analytics'})
    
    @socketio.on('save_calibration_sample')
    def handle_save_calibration_sample(data):
        """Save a calibration sample for user"""
        try:
            user_id = user_sessions.get(request.sid)
            if not user_id:
                emit('error', {'message': 'User not logged in'})
                return
            
            from emotion_calibration import calibrator
            import base64
            
            emotion = data.get('emotion')
            frame_data_b64 = data.get('frame_data')
            
            if not emotion or not frame_data_b64:
                emit('error', {'message': 'Missing emotion or frame data'})
                return
            
            # Decode base64 frame data
            frame_data = base64.b64decode(frame_data_b64)
            
            # Save calibration sample
            success = asyncio.run(calibrator.save_calibration_sample(user_id, emotion, frame_data))
            
            if success:
                emit('calibration_sample_saved', {'emotion': emotion})
                logger.info(f"Calibration sample saved for user {user_id}, emotion: {emotion}")
            else:
                emit('error', {'message': 'Failed to save calibration sample'})
                
        except Exception as e:
            logger.error(f"Calibration sample save error: {e}")
            emit('error', {'message': 'Failed to save calibration sample'})
    
    @socketio.on('check_calibration')
    def handle_check_calibration():
        """Check if user has calibration data"""
        try:
            user_id = user_sessions.get(request.sid)
            if not user_id:
                emit('error', {'message': 'User not logged in'})
                return
            
            from emotion_calibration import calibrator
            
            has_calibration = asyncio.run(calibrator.has_calibration(user_id))
            emit('calibration_status', {'has_calibration': has_calibration})
            
        except Exception as e:
            logger.error(f"Check calibration error: {e}")
            emit('error', {'message': 'Failed to check calibration'})
    
    @socketio.on('clear_calibration')
    def handle_clear_calibration():
        """Clear user's calibration data"""
        try:
            user_id = user_sessions.get(request.sid)
            if not user_id:
                emit('error', {'message': 'User not logged in'})
                return
            
            from emotion_calibration import calibrator
            
            asyncio.run(calibrator.clear_calibration(user_id))
            emit('calibration_cleared', {'message': 'Calibration data cleared'})
            logger.info(f"Calibration cleared for user {user_id}")
            
        except Exception as e:
            logger.error(f"Clear calibration error: {e}")
            emit('error', {'message': 'Failed to clear calibration'})
    
    return socketio

