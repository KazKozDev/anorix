#!/usr/bin/env python3
"""
Local Friend Web UI - Flask Server
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# Ensure we're working from project root and add it to path
project_root = Path(__file__).parent.parent.resolve()
os.chdir(project_root)  # Change working directory to project root
sys.path.insert(0, str(project_root))

try:
    from src.core.agent import VirtualFriend
    from src.core.voice_engine import WebRTCVoiceServer
    import yaml
    VOICE_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Voice engine not available - running in text-only mode")
    VirtualFriend = None
    WebRTCVoiceServer = None
    VOICE_ENGINE_AVAILABLE = False

# Configure logging (force clears any existing handlers to avoid duplicates)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True,
)
logger = logging.getLogger(__name__)

# Flask app setup - use absolute paths for templates and static
web_ui_dir = Path(__file__).parent
app = Flask(__name__, 
           template_folder=str(web_ui_dir / 'templates'),
           static_folder=str(web_ui_dir / 'static'))
app.config['SECRET_KEY'] = 'local-friend-secret-key-change-in-production'

# Enable CORS for development
CORS(app)

# Socket.IO for real-time WebRTC communication
socketio = SocketIO(app, cors_allowed_origins="*")

# Global instances
friend_instance = None
voice_server = None

# Load configuration from YAML file
def load_config():
    """Load configuration from config/friend_config.yaml"""
    config_path = Path("config/friend_config.yaml")
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return {
                'model_name': config['llm']['model_name'],
                'friend_name': config['friend']['name'],
                'temperature': config['llm']['temperature'],
                'verbose': config['logging']['level'] == 'DEBUG'
            }
        else:
            logger.warning(f"Config file not found: {config_path}, using defaults")
    except Exception as e:
        logger.error(f"Error loading config: {e}, using defaults")
    
    # Default fallback config
    return {
        'friend_name': 'Anorix',
        'verbose': True
    }

friend_config = load_config()
logger.info(f"Loaded config: {friend_config}")

from src.core.config.settings import load_llm_settings

def initialize_friend():
    """Initialize the virtual friend."""
    global friend_instance
    
    if not VirtualFriend:
        logger.error("❌ VirtualFriend not available")
        return False
    
    try:
        if friend_instance is not None:
            logger.info("Virtual Friend already initialized - skipping")
            return True
        logger.info("Initializing Virtual Friend...")
        llm_settings = load_llm_settings()
        friend_instance = VirtualFriend(
            model_name=llm_settings.get('model_name'),
            temperature=llm_settings.get('temperature'),
            verbose=friend_config['verbose'],
            friend_name=friend_config['friend_name']
        )
        logger.info("✅ Virtual Friend initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Virtual Friend: {e}")
        return False

async def initialize_voice_server():
    """Initialize the voice server."""
    global voice_server
    
    if not VOICE_ENGINE_AVAILABLE:
        logger.warning("⚠️ Voice engine not available - running in text-only mode")
        return False
    
    try:
        if voice_server is not None:
            logger.info("Voice Server already initialized - skipping")
            return True
        logger.info("Initializing Voice Server...")
        voice_server = WebRTCVoiceServer(
            friend_instance=friend_instance,
            socketio_instance=socketio,  # Pass socketio instance
            verbose=friend_config['verbose']
        )
        logger.info("✅ Voice Server initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Voice Server: {e}")
        return False

def get_friend_stats() -> Dict[str, Any]:
    """Get current friend statistics."""
    if not friend_instance:
        return {
            'online': False,
            'memory_count': 0,
            'conversation_count': 0,
            'mood': 'Unavailable'
        }
    
    try:
        # Get memory count from RAG collection info
        memory_count = 0
        try:
            if hasattr(friend_instance, 'tool_manager') and getattr(friend_instance.tool_manager, 'rag_tool', None):
                info = friend_instance.tool_manager.rag_tool.get_collection_info()
                memory_count = info.get('document_count', 0) if isinstance(info, dict) else 0
        except Exception:
            memory_count = 0
        
        # Conversation count not tracked via RAG; keep 0 or compute via logs later
        conversation_count = 0
        
        # Get recent mood
        emotion_data = friend_instance.emotional_intelligence.emotion_data
        recent_moods = friend_instance.emotional_intelligence._get_recent_moods(days=1)
        current_mood = recent_moods[-1]['emotion'] if recent_moods else 'Neutral'
        
        return {
            'online': True,
            'memory_count': memory_count,
            'conversation_count': conversation_count,
            'mood': current_mood,
            'status_text': 'Ready to chat'
        }
        
    except Exception as e:
        logger.error(f"Error getting friend stats: {e}")
        return {
            'online': True,
            'memory_count': 0,
            'conversation_count': 0,
            'mood': 'Unknown',
            'error': str(e)
        }

# Routes

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Get friend status."""
    try:
        stats = get_friend_stats()
        
        if friend_instance:
            # Add detailed memory and mood info
            try:
                # Recent user facts via RAG are not directly enumerable without queries; provide collection info
                if hasattr(friend_instance, 'tool_manager') and getattr(friend_instance.tool_manager, 'rag_tool', None):
                    stats['rag_info'] = friend_instance.tool_manager.rag_tool.get_collection_info()
                
                # Mood history
                recent_moods = friend_instance.emotional_intelligence._get_recent_moods(days=7)
                stats['mood_history'] = recent_moods
                
            except Exception as e:
                logger.warning(f"Error getting detailed stats: {e}")
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error in status endpoint: {e}")
        return jsonify({
            'online': False,
            'error': str(e)
        }), 500

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Chat with friend."""
    if not friend_instance:
        return jsonify({
            'error': 'Virtual Friend is not initialized',
            'message': 'Sorry, I am unavailable right now. Please try again later.'
        }), 503
    
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Missing message'
            }), 400
        
        message = data['message'].strip()
        if not message:
            return jsonify({
                'error': 'Empty message'
            }), 400
        
        voice_mode = data.get('voice_mode', False)
        
        logger.info(f"💬 Received message: {message[:50]}..." + ("(voice)" if voice_mode else ""))
        
        # Pre-process: handle local file ingestion commands to avoid LLM refusing local access
        try:
            lowered = message.lower()
            file_path_to_read: Optional[str] = None
            # English pattern: "Read file: <path>"
            if lowered.startswith("read file:"):
                file_path_to_read = message.split(":", 1)[1].strip()

            if file_path_to_read:
                p = Path(file_path_to_read).expanduser()
                if p.exists() and p.is_file():
                    # Ingest via RAG management tool
                    rm_tool = friend_instance.tool_manager.get_tool('rag_management') if hasattr(friend_instance, 'tool_manager') else None
                    if rm_tool:
                        result = rm_tool.func(action='add_file', path=str(p))
                        logger.info(f"RAG add_file result: {result}")
                        response = (
                            f"File added to knowledge base (RAG): {p.name}. "
                            f"I can now search its content. You can ask a question about the file!"
                        )
                    else:
                        response = "RAG tool is temporarily unavailable. Please try again later."
                else:
                    response = "Could not find a file at the specified path. Please ensure the path is correct and the file exists."
            else:
                # Process message with friend normally
                response = friend_instance.process_query(message)
        except Exception as e:
            logger.error(f"Pre-processing error in chat: {e}")
            response = friend_instance.process_query(message)
        
        # Get updated stats
        stats = get_friend_stats()
        
        logger.info(f"🤖 Friend response: {response[:100]}...")
        
        return jsonify({
            'message': response,
            'stats': stats,
            'voice_mode': voice_mode,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({
            'error': f'Message processing error: {str(e)}',
            'message': 'Sorry, an error occurred while processing your message.'
        }), 500

@app.route('/api/memory')
def api_memory():
    """Get memory information."""
    if not friend_instance:
        return jsonify({'error': 'Friend not initialized'}), 503
    
    try:
        # Return RAG collection info only (personal_memory removed)
        rag_info = {}
        try:
            if hasattr(friend_instance, 'tool_manager') and getattr(friend_instance.tool_manager, 'rag_tool', None):
                rag_info = friend_instance.tool_manager.rag_tool.get_collection_info()
        except Exception:
            rag_info = {'error': 'RAG info unavailable'}
        return jsonify({'rag_info': rag_info})
    
    except Exception as e:
        logger.error(f"Error in memory endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mood')
def api_mood():
    """Get mood information."""
    if not friend_instance:
        return jsonify({'error': 'Friend not initialized'}), 503
    
    try:
        mood_history = friend_instance.emotional_intelligence._get_mood_history()
        recent_moods = friend_instance.emotional_intelligence._get_recent_moods(days=7)
        
        return jsonify({
            'history': mood_history,
            'recent_moods': recent_moods
        })
        
    except Exception as e:
        logger.error(f"Error in mood endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/personality')
def api_personality():
    """Get personality information."""
    if not friend_instance:
        return jsonify({'error': 'Friend not initialized'}), 503
    
    try:
        personality_profile = friend_instance.personality_system._get_personality_profile()
        friend_info = friend_instance.personality_system._get_friend_info()
        
        return jsonify({
            'profile': personality_profile,
            'friend_info': friend_info
        })
        
    except Exception as e:
        logger.error(f"Error in personality endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset-memory', methods=['POST'])
def api_reset_memory():
    """Reset friend memory."""
    if not friend_instance:
        return jsonify({'error': 'Friend not initialized'}), 503
    
    try:
        # Reset conversation memory
        friend_instance.reset_memory()
        
        # Do not clear RAG knowledge base here to preserve accumulated facts
        
        # Clear emotional data
        emotion_file = friend_instance.emotional_intelligence.emotion_file
        if emotion_file.exists():
            emotion_file.unlink()
        friend_instance.emotional_intelligence.emotion_data = friend_instance.emotional_intelligence._create_empty_emotion_data()
        friend_instance.emotional_intelligence._save_emotion_data()
        
        logger.info("🧹 Memory reset completed")
        
        return jsonify({
            'success': True,
            'message': 'Memory cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Error resetting memory: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """Get or update friend configuration."""
    global friend_config
    
    if request.method == 'GET':
        return jsonify(friend_config)
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Update config
            if 'friend_name' in data:
                friend_config['friend_name'] = data['friend_name']
            
            if 'model_name' in data:
                friend_config['model_name'] = data['model_name']
            
            if 'temperature' in data:
                friend_config['temperature'] = float(data['temperature'])
            
            # Note: Changing config requires restart for full effect
            logger.info(f"Config updated: {friend_config}")
            
            return jsonify({
                'success': True,
                'config': friend_config,
                'note': 'Some changes require restart'
            })
            
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def api_health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'friend_initialized': friend_instance is not None,
        'voice_server_initialized': voice_server is not None,
        'voice_engine_available': VOICE_ENGINE_AVAILABLE,
        'timestamp': datetime.now().isoformat()
    })

# WebRTC Voice Endpoints

@app.route('/api/voice/create-session', methods=['POST'])
async def api_create_voice_session():
    """Create new WebRTC voice session."""
    if not voice_server:
        return jsonify({'error': 'Voice server not initialized'}), 503
    
    try:
        data = request.get_json() or {}
        session_id = await voice_server.create_session(data.get('config'))
        
        logger.info(f"🎙️ Created voice session: {session_id}")
        
        return jsonify({
            'session_id': session_id,
            'status': 'created'
        })
        
    except Exception as e:
        logger.error(f"Error creating voice session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/offer', methods=['POST'])
async def api_voice_offer():
    """Handle WebRTC offer."""
    if not voice_server:
        return jsonify({'error': 'Voice server not initialized'}), 503
    
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        offer_sdp = data.get('offer')
        
        if not session_id or not offer_sdp:
            return jsonify({'error': 'Missing session_id or offer'}), 400
        
        answer_sdp = await voice_server.handle_offer(session_id, offer_sdp)
        
        logger.info(f"📞 Handled WebRTC offer for session {session_id}")
        
        return jsonify({
            'answer': answer_sdp,
            'status': 'answered'
        })
        
    except Exception as e:
        logger.error(f"Error handling WebRTC offer: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/session/<session_id>')
async def api_voice_session_info(session_id):
    """Get voice session information."""
    if not voice_server:
        return jsonify({'error': 'Voice server not initialized'}), 503
    
    try:
        info = await voice_server.get_session_info(session_id)
        return jsonify(info)
        
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/sessions')
async def api_voice_sessions():
    """List all voice sessions."""
    if not voice_server:
        return jsonify({'error': 'Voice server not initialized'}), 503
    
    try:
        sessions = await voice_server.list_sessions()
        return jsonify(sessions)
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return jsonify({'error': str(e)}), 500

# Error handlers

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# Static files for development
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

# Socket.IO Event Handlers for WebRTC Signaling

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"🔗 Client connected: {request.sid}")
    emit('status', {
        'connected': True,
        'voice_available': VOICE_ENGINE_AVAILABLE,
        'friend_available': friend_instance is not None
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"🔌 Client disconnected: {request.sid}")

@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    """Handle WebRTC offer from client."""
    try:
        if not voice_server:
            emit('webrtc_error', {'error': 'Voice server not initialized'})
            return
        
        session_id = data.get('session_id')
        offer_sdp = data.get('offer')
        
        if not session_id or not offer_sdp:
            emit('webrtc_error', {'error': 'Missing session_id or offer'})
            return
        
        # Run async operation in event loop
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Handle offer
        answer_sdp = loop.run_until_complete(voice_server.handle_offer(session_id, offer_sdp))
        
        # Send answer back to client
        emit('webrtc_answer', {
            'session_id': session_id,
            'answer': answer_sdp
        })
        
        logger.info(f"📞 Handled WebRTC offer via Socket.IO for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error handling WebRTC offer: {e}")
        emit('webrtc_error', {'error': str(e)})

@socketio.on('create_voice_session')
def handle_create_voice_session(data):
    """Create new voice session via Socket.IO."""
    try:
        if not voice_server:
            emit('voice_error', {'error': 'Voice server not initialized'})
            return
        
        config = data.get('config', {})
        
        # Run async operation in event loop
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        session_id = loop.run_until_complete(voice_server.create_session(config))
        
        emit('voice_session_created', {
            'session_id': session_id,
            'status': 'created'
        })
        
        logger.info(f"🎙️ Created voice session via Socket.IO: {session_id}")
        
    except Exception as e:
        logger.error(f"Error creating voice session: {e}")
        emit('voice_error', {'error': str(e)})

@socketio.on('text_to_speech')
def handle_text_to_speech(data):
    """Convert text to speech for active session."""
    try:
        if not voice_server:
            emit('tts_error', {'error': 'Voice server not initialized'})
            return
        
        session_id = data.get('session_id')
        text = data.get('text')
        
        if not session_id or not text:
            emit('tts_error', {'error': 'Missing session_id or text'})
            return
        
        # Run async operation in event loop
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(voice_server.send_text_to_session(session_id, text))
        
        emit('tts_success', {
            'session_id': session_id,
            'text': text[:50] + '...' if len(text) > 50 else text
        })
        
        logger.info(f"🗣️ Sent text to speech for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}")
        emit('tts_error', {'error': str(e)})

def main():
    """Main function to run the server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Local Friend Web UI Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--model', default=None, help='Ollama model name (default: from env or config)')
    parser.add_argument('--friend-name', default='Anorix', help='Friend name')
    parser.add_argument('--no-init', action='store_true', help='Skip friend initialization')
    
    args = parser.parse_args()
    
    # Update config from args
    friend_config['model_name'] = args.model
    friend_config['friend_name'] = args.friend_name
    
    print(f"🚀 Starting Local Friend Web UI Server")
    print(f"📍 Host: {args.host}:{args.port}")
    print(f"🤖 Friend: {friend_config['friend_name']}")
    print(f"🧠 Model: {friend_config['model_name']}")
    print(f"🔧 Debug: {args.debug}")
    
    if not args.no_init:
        print("\n" + "="*50)
        success = initialize_friend()
        
        # Initialize voice server if friend is available
        if success and VOICE_ENGINE_AVAILABLE:
            print("🔄 Initializing Voice Server...")
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                voice_success = loop.run_until_complete(initialize_voice_server())
                if voice_success:
                    print("✅ Voice Server initialized")
                else:
                    print("⚠️  Voice Server initialization failed")
            except Exception as e:
                print(f"⚠️  Voice Server initialization error: {e}")
        
        print("="*50)
        
        if not success:
            print("⚠️  Friend initialization failed, but server will start anyway")
            print("   You can try to initialize later through the API")
    else:
        print("⏭️  Skipping friend initialization")
    
    print(f"\n🌐 Opening http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        socketio.run(
            app,
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=False  # Prevent double initialization that causes duplicate logs
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == '__main__':
    main()