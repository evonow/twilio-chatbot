"""
Web Application for Email & SMS Data Processing
Provides a GUI for uploading, processing, and managing the knowledge base
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, Response, session, redirect, url_for
# Railway deployment - variables configured
from werkzeug.utils import secure_filename
from twilio.twiml.messaging_response import MessagingResponse
from functools import wraps
import os
import json
import sys
from dotenv import load_dotenv
from data_processor import DataProcessor
from chatbot import ChatbotAgent
import threading
from datetime import datetime, timedelta
import hashlib

# Add scripts directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
try:
    from google_docs_connector import GoogleDocsConnector
    GOOGLE_DOCS_AVAILABLE = True
except ImportError:
    GOOGLE_DOCS_AVAILABLE = False

try:
    from gitlab_connector import GitLabConnector
    GITLAB_AVAILABLE = True
except ImportError:
    GITLAB_AVAILABLE = False

load_dotenv()

app = Flask(__name__)

# Use persistent data directory (for Railway volumes or local storage)
DATA_DIR = os.getenv('DATA_DIR', './data')
os.makedirs(DATA_DIR, exist_ok=True)

app.config['UPLOAD_FOLDER'] = os.path.join(DATA_DIR, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Sessions last 24 hours

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# User management file (in persistent data directory)
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

# Ensure users file exists with default admin
def init_users_file():
    """Initialize users file with default admin if it doesn't exist"""
    if not os.path.exists(USERS_FILE):
        default_users = {
            'users': [
                {
                    'pin': '0000',
                    'name': 'Admin',
                    'role': 'Admin',
                    'created_at': datetime.now().isoformat()
                }
            ]
        }
        with open(USERS_FILE, 'w') as f:
            json.dump(default_users, f, indent=2)

init_users_file()

def load_users():
    """Load users from JSON file"""
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f).get('users', [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump({'users': users}, f, indent=2)

def hash_pin(pin):
    """Hash PIN for storage (simple hash, in production use bcrypt)"""
    return hashlib.sha256(pin.encode()).hexdigest()

def verify_pin(pin, hashed_pin):
    """Verify PIN against hash"""
    return hash_pin(pin) == hashed_pin

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_pin' not in session:
            return jsonify({'error': 'Authentication required', 'redirect': '/login'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin (Admin role)"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if session.get('user_role') != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Allowed file extensions
ALLOWED_EXTENSIONS = {'eml', 'mbox', 'txt', 'json', 'csv', 'xml', 'docx', 'pdf'}

# Global processing status
processing_status = {
    'is_processing': False,
    'current_file': None,
    'files_processed': 0,
    'total_files': 0,
    'documents_added': 0,
    'errors': []
}

# Global conversation history storage (phone_number -> list of messages)
# Format: {'phone_number': [{'role': 'user'|'assistant', 'content': '...', 'timestamp': '...'}, ...]}
twilio_conversations = {}

# Conversation history storage (session-based)
# In production, use Redis or database instead
conversation_history = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page"""
    if 'user_pin' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', user_role=session.get('user_role'), user_name=session.get('user_name'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        data = request.get_json()
        pin = data.get('pin', '').strip()
        
        if not pin or len(pin) != 4 or not pin.isdigit():
            return jsonify({'error': 'Invalid PIN. Must be 4 digits.'}), 400
        
        users = load_users()
        for user in users:
            # Check if PIN matches (stored as hash or plain for now)
            if 'hashed_pin' in user:
                if verify_pin(pin, user['hashed_pin']):
                    session.permanent = True
                    session['user_pin'] = user['pin']  # Store original PIN for reference
                    session['user_role'] = user['role']
                    session['user_name'] = user.get('name', 'User')
                    return jsonify({
                        'success': True,
                        'message': 'Login successful',
                        'role': user['role'],
                        'name': user.get('name', 'User')
                    })
            else:
                # Backward compatibility: plain PIN
                if user['pin'] == pin:
                    session.permanent = True
                    session['user_pin'] = user['pin']
                    session['user_role'] = user['role']
                    session['user_name'] = user.get('name', 'User')
                    # Upgrade to hashed PIN
                    user['hashed_pin'] = hash_pin(pin)
                    save_users(users)
                    return jsonify({
                        'success': True,
                        'message': 'Login successful',
                        'role': user['role'],
                        'name': user.get('name', 'User')
                    })
        
        return jsonify({'error': 'Invalid PIN'}), 401
    
    # GET request - show login page
    if 'user_pin' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    """Logout"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/auth/status')
def auth_status():
    """Get current authentication status"""
    if 'user_pin' in session:
        return jsonify({
            'authenticated': True,
            'role': session.get('user_role'),
            'name': session.get('user_name')
        })
    return jsonify({'authenticated': False})

@app.route('/api/users', methods=['GET'])
@admin_required
def list_users():
    """List all users (admin only)"""
    users = load_users()
    # Don't return PINs or hashed PINs
    safe_users = []
    for user in users:
        safe_users.append({
            'pin': user['pin'],  # Show PIN for admin management
            'name': user.get('name', ''),
            'role': user['role'],
            'created_at': user.get('created_at', '')
        })
    return jsonify({'users': safe_users})

@app.route('/api/users', methods=['POST'])
@admin_required
def create_user():
    """Create a new user (admin only)"""
    data = request.get_json()
    pin = data.get('pin', '').strip()
    name = data.get('name', '').strip()
    role = data.get('role', '').strip()
    
    if not pin or len(pin) != 4 or not pin.isdigit():
        return jsonify({'error': 'PIN must be exactly 4 digits'}), 400
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    if role not in ['Admin', 'Internal', 'Customer', 'Sales Rep']:
        return jsonify({'error': 'Invalid role. Must be: Admin, Internal, Customer, or Sales Rep'}), 400
    
    users = load_users()
    
    # Check if PIN already exists
    if any(u['pin'] == pin for u in users):
        return jsonify({'error': 'PIN already exists'}), 400
    
    # Create new user
    new_user = {
        'pin': pin,
        'hashed_pin': hash_pin(pin),
        'name': name,
        'role': role,
        'created_at': datetime.now().isoformat()
    }
    users.append(new_user)
    save_users(users)
    
    return jsonify({
        'success': True,
        'message': 'User created successfully',
        'user': {
            'pin': pin,
            'name': name,
            'role': role
        }
    })

@app.route('/api/users/<pin>', methods=['PUT'])
@admin_required
def update_user(pin):
    """Update a user (admin only)"""
    data = request.get_json()
    name = data.get('name', '').strip()
    role = data.get('role', '').strip()
    new_pin = data.get('pin', '').strip()
    
    users = load_users()
    user_found = False
    
    for user in users:
        if user['pin'] == pin:
            user_found = True
            if name:
                user['name'] = name
            if role and role in ['Admin', 'Internal', 'Customer', 'Sales Rep']:
                user['role'] = role
            if new_pin and len(new_pin) == 4 and new_pin.isdigit():
                # Check if new PIN already exists
                if any(u['pin'] == new_pin and u['pin'] != pin for u in users):
                    return jsonify({'error': 'New PIN already exists'}), 400
                user['pin'] = new_pin
                user['hashed_pin'] = hash_pin(new_pin)
            break
    
    if not user_found:
        return jsonify({'error': 'User not found'}), 404
    
    save_users(users)
    return jsonify({'success': True, 'message': 'User updated successfully'})

@app.route('/api/users/<pin>', methods=['DELETE'])
@admin_required
def delete_user(pin):
    """Delete a user (admin only)"""
    users = load_users()
    original_count = len(users)
    users = [u for u in users if u['pin'] != pin]
    
    if len(users) == original_count:
        return jsonify({'error': 'User not found'}), 404
    
    # Don't allow deleting the last user
    if len(users) == 0:
        return jsonify({'error': 'Cannot delete the last user'}), 400
    
    save_users(users)
    return jsonify({'success': True, 'message': 'User deleted successfully'})

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_files():
    """Handle file uploads"""
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    uploaded_files = []
    
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            uploaded_files.append({
                'filename': filename,
                'original_name': file.filename,
                'size': os.path.getsize(filepath)
            })
    
    if not uploaded_files:
        return jsonify({'error': 'No valid files uploaded'}), 400
    
    return jsonify({
        'success': True,
        'files': uploaded_files,
        'message': f'Successfully uploaded {len(uploaded_files)} file(s)'
    })

@app.route('/api/process', methods=['POST'])
@login_required
def process_files():
    """Process uploaded files"""
    global processing_status
    
    if processing_status['is_processing']:
        return jsonify({'error': 'Processing already in progress'}), 400
    
    data = request.json
    files = data.get('files', [])
    audience = data.get('audience')  # 'sales_reps', 'customers', 'internal', or None
    
    if not files:
        return jsonify({'error': 'No files specified'}), 400
    
    # Reset status
    processing_status = {
        'is_processing': True,
        'current_file': None,
        'files_processed': 0,
        'total_files': len(files),
        'documents_added': 0,
        'errors': []
    }
    
    # Start processing in background thread
    thread = threading.Thread(target=process_files_background, args=(files, audience))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Processing started',
        'total_files': len(files)
    })

@app.route('/api/process/all', methods=['POST'])
@login_required
def process_all_files():
    """Process all files in the uploads directory"""
    global processing_status
    
    if processing_status['is_processing']:
        return jsonify({'error': 'Processing already in progress'}), 400
    
    data = request.json or {}
    audience = data.get('audience')  # 'sales_reps', 'customers', 'internal', or None
    
    upload_dir = app.config['UPLOAD_FOLDER']
    
    # Get all files from upload directory
    all_files = []
    if os.path.exists(upload_dir):
        for filename in os.listdir(upload_dir):
            filepath = os.path.join(upload_dir, filename)
            if os.path.isfile(filepath):
                # Only include supported file types
                if allowed_file(filename):
                    all_files.append({
                        'filename': filename,
                        'size': os.path.getsize(filepath)
                    })
    
    if not all_files:
        return jsonify({'error': 'No files found in uploads directory'}), 400
    
    # Reset status
    processing_status = {
        'is_processing': True,
        'current_file': None,
        'files_processed': 0,
        'total_files': len(all_files),
        'documents_added': 0,
        'errors': []
    }
    
    # Start processing in background thread
    thread = threading.Thread(target=process_files_background, args=(all_files, audience))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': f'Processing started for {len(all_files)} file(s)',
        'total_files': len(all_files)
    })

def process_files_background(files, audience=None):
    """Process files in background"""
    global processing_status
    
    processor = DataProcessor()
    
    try:
        for file_info in files:
            filename = file_info.get('filename')
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            if not os.path.exists(filepath):
                processing_status['errors'].append(f"File not found: {filename}")
                continue
            
            processing_status['current_file'] = filename
            
            try:
                # Determine file type and process
                if filename.endswith('.mbox'):
                    documents = processor.process_mbox_file(filepath, audience=audience)
                elif filename.endswith('.eml'):
                    documents = processor.process_email_file(filepath, audience=audience)
                elif filename.endswith('.docx'):
                    documents = processor.process_word_document(filepath, audience=audience)
                elif filename.endswith('.pdf'):
                    documents = processor.process_pdf_document(filepath, audience=audience)
                elif filename.endswith('.xml'):
                    documents = processor.process_text_message_file(filepath, audience=audience)
                elif filename.endswith('.csv'):
                    documents = processor.process_text_message_file(filepath, audience=audience)
                elif filename.endswith('.json'):
                    documents = processor.process_text_message_file(filepath, audience=audience)
                elif filename.endswith('.txt'):
                    # Try to determine if it's email or SMS
                    if 'email' in filename.lower() or 'mail' in filename.lower():
                        documents = processor.process_email_file(filepath, audience=audience)
                    else:
                        documents = processor.process_text_message_file(filepath, audience=audience)
                else:
                    documents = processor.process_email_file(filepath, audience=audience)
                
                # Add documents to knowledge base
                for doc in documents:
                    doc_id = f"{filename}_{doc['metadata'].get('chunk_index', 0)}"
                    processor.chatbot.add_document(
                        text=doc['text'],
                        metadata=doc['metadata'],
                        doc_id=doc_id
                    )
                    processing_status['documents_added'] += 1
                
                processing_status['files_processed'] += 1
                
            except Exception as e:
                error_msg = f"Error processing {filename}: {str(e)}"
                processing_status['errors'].append(error_msg)
                print(error_msg)
    
    finally:
        processing_status['is_processing'] = False
        processing_status['current_file'] = None

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get processing status"""
    return jsonify(processing_status)

@app.route('/api/query', methods=['POST'])
@login_required
def query_chatbot():
    """Query the chatbot with conversation history"""
    data = request.json
    query = data.get('query', '').strip()
    session_id = data.get('session_id', 'default')  # Use session_id to maintain conversation
    user_role = session.get('user_role', '')
    
    # Enforce audience filtering based on user role
    requested_audience = data.get('audience', '')
    
    # Admin: can access everything (no filtering)
    if user_role == 'Admin':
        audience_filter = requested_audience  # Use requested filter or empty for all
    # Internal: can access all roles (no filtering)
    elif user_role == 'Internal':
        audience_filter = ''  # No filtering, can access all
    # Sales Rep: only sales_reps
    elif user_role == 'Sales Rep':
        audience_filter = 'sales_reps'
    # Customer: only customers
    elif user_role == 'Customer':
        audience_filter = 'customers'
    else:
        # Default: no access (shouldn't happen, but safety)
        audience_filter = ''
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        chatbot = ChatbotAgent()
        
        # Get conversation history for this session
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        history = conversation_history[session_id]
        
        # Use the enforced audience filter based on user role (set earlier)
        # Get response with conversation history and optional audience filtering
        response, sources = chatbot.get_response_with_sources(query, history, audience=audience_filter)
        
        # Add to conversation history
        conversation_history[session_id].append({
            'role': 'user',
            'content': query
        })
        conversation_history[session_id].append({
            'role': 'assistant',
            'content': response
        })
        
        # Keep only last 10 exchanges (20 messages) to avoid token limits
        if len(conversation_history[session_id]) > 20:
            conversation_history[session_id] = conversation_history[session_id][-20:]
        
        return jsonify({
            'success': True,
            'response': response,
            'query': query,
            'sources': sources,
            'session_id': session_id
        })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error in query_chatbot: {e}")
        print(f"Traceback:\n{error_traceback}")
        # Return simplified error to user, but log full traceback
        return jsonify({
            'error': str(e),
            'details': error_traceback.split('\n')[-5:] if 'proxies' in str(e) else None
        }), 500

@app.route('/api/conversation/clear', methods=['POST'])
@login_required
def clear_conversation():
    """Clear conversation history for a session"""
    data = request.json
    session_id = data.get('session_id', 'default')
    
    if session_id in conversation_history:
        conversation_history[session_id] = []
    
    return jsonify({
        'success': True,
        'message': 'Conversation history cleared'
    })

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Get knowledge base statistics"""
    try:
        chatbot = ChatbotAgent()
        collection = chatbot.collection
        
        # Get collection count
        count_result = collection.count()
        
        return jsonify({
            'success': True,
            'total_documents': count_result,
            'collection_name': chatbot.collection.name
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Test Email Ingestion search endpoint removed

@app.route('/api/examples', methods=['GET'])
@login_required
def get_example_questions():
    """Get example questions from the knowledge base for placeholder text"""
    try:
        chatbot = ChatbotAgent()
        user_role = session.get('user_role', '')
        
        # Get audience filter based on user role
        if user_role == 'Admin':
            audience_filter = None  # Admin can see all
        elif user_role == 'Internal':
            audience_filter = None  # Internal can see all
        elif user_role == 'Sales Rep':
            audience_filter = 'sales_reps'
        elif user_role == 'Customer':
            audience_filter = 'customers'
        else:
            audience_filter = None
        
        # Get sample documents from knowledge base
        try:
            # Use a generic query to get sample documents
            sample_query = "customer question help support"
            sample_docs = chatbot._retrieve_relevant_context(sample_query, n_results=20, audience=audience_filter)
            
            # Extract questions from sample documents
            import re
            questions = []
            question_patterns = [
                r'(?:how|what|why|when|where|can|could|would|will|do|does|did|is|are|was|were)\s+[^?.!]+[?]',
                r'I\s+(?:can\'?t|cannot|need|want|would like|am trying|am having trouble)\s+[^?.!]+[?.!]',
                r'(?:help|assist|support).*[?]',
            ]
            
            for doc in sample_docs:
                text = doc.get('text', '')
                for pattern in question_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        question = match.strip()
                        # Clean up and validate
                        if len(question) > 15 and len(question) < 100:
                            # Remove extra whitespace and clean
                            question = ' '.join(question.split())
                            if question not in questions:
                                questions.append(question)
                                if len(questions) >= 5:
                                    break
                if len(questions) >= 5:
                    break
            
            # If we don't have enough questions, use fallback examples
            if len(questions) < 3:
                questions = [
                    "How do I create a fundraiser?",
                    "How do I delete my profile?",
                    "How do I add a donor?",
                    "How do I track donations?",
                    "How do I share my fundraiser?"
                ]
            
            return jsonify({
                'success': True,
                'examples': questions[:5]  # Return top 5 examples
            })
        except Exception as e:
            print(f"Error getting examples: {e}")
            # Return fallback examples
            return jsonify({
                'success': True,
                'examples': [
                    "How do I create a fundraiser?",
                    "How do I delete my profile?",
                    "How do I add a donor?",
                    "How do I track donations?",
                    "How do I share my fundraiser?"
                ]
            })
    except Exception as e:
        return jsonify({
            'success': True,
            'examples': [
                "How do I create a fundraiser?",
                "How do I delete my profile?",
                "How do I add a donor?"
            ]
        })

@app.route('/api/analyze/faqs', methods=['GET'])
@login_required
def analyze_faqs():
    """Analyze knowledge base to extract frequently asked questions"""
    try:
        chatbot = ChatbotAgent()
        
        # Get parameters
        max_questions = request.args.get('max_questions', 20, type=int)
        sample_size = request.args.get('sample_size', 100, type=int)
        
        faqs = chatbot.analyze_frequently_asked_questions(
            max_questions=max_questions,
            sample_size=sample_size
        )
        
        return jsonify({
            'success': True,
            'faqs': faqs,
            'count': len(faqs)
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/clear', methods=['POST'])
@admin_required
def clear_knowledge_base():
    """Clear the knowledge base (use with caution!)"""
    try:
        chatbot = ChatbotAgent()
        # Delete all vectors from Pinecone index
        index_name = chatbot.index_name if hasattr(chatbot, 'index_name') else 'customer-service-kb'
        # Delete all vectors by deleting the index and recreating it
        # Note: This requires admin access to Pinecone
        # Alternative: Delete all vectors using delete_all() if available
        try:
            # Try to delete all vectors using delete_all (if supported)
            chatbot.index.delete(delete_all=True)
        except:
            # Fallback: Delete index and recreate (requires Pinecone admin API)
            # For now, just return an error suggesting manual deletion
            return jsonify({
                'error': 'Cannot automatically clear Pinecone index. Please delete all vectors manually in Pinecone dashboard or delete and recreate the index.'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Knowledge base cleared successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files', methods=['GET'])
@login_required
def list_uploaded_files():
    """List uploaded files with processing status"""
    files = []
    upload_dir = app.config['UPLOAD_FOLDER']
    
    # Get list of processed files from knowledge base and their audiences
    processed_files = set()
    file_audiences = {}  # Map filename -> audience
    try:
        chatbot = ChatbotAgent()
        # Get all documents and extract unique filenames and audiences
        all_docs = chatbot.collection.get(limit=10000)  # Get a large number
        if all_docs and all_docs.get('metadatas'):
            for metadata in all_docs['metadatas']:
                if metadata and 'file' in metadata:
                    # Extract original filename (remove timestamp prefix if present)
                    filename = metadata['file']
                    # Also check for timestamp-prefixed versions
                    processed_files.add(filename)
                    
                    # Store audience if present
                    if 'audience' in metadata and metadata['audience']:
                        if filename not in file_audiences:
                            file_audiences[filename] = metadata['audience']
                    
                    # Try to match timestamp-prefixed versions
                    if '_' in filename:
                        # Check if it matches uploaded file pattern
                        parts = filename.split('_', 2)
                        if len(parts) >= 3 and parts[0].isdigit() and len(parts[0]) == 8:
                            # This is a timestamp-prefixed file, add both versions
                            original_name = '_'.join(parts[2:])
                            processed_files.add(original_name)
                            # Also map audience to original name
                            if 'audience' in metadata and metadata['audience']:
                                if original_name not in file_audiences:
                                    file_audiences[original_name] = metadata['audience']
    except Exception as e:
        print(f"Error getting processed files: {e}")
    
    if os.path.exists(upload_dir):
        for filename in os.listdir(upload_dir):
            filepath = os.path.join(upload_dir, filename)
            if os.path.isfile(filepath):
                # Only include allowed file types
                if not allowed_file(filename):
                    continue
                
                # Check if this file has been processed
                is_processed = filename in processed_files
                # Also check without timestamp prefix
                if not is_processed and '_' in filename:
                    parts = filename.split('_', 2)
                    if len(parts) >= 3 and parts[0].isdigit() and len(parts[0]) == 8:
                        original_name = '_'.join(parts[2:])
                        is_processed = original_name in processed_files
                
                # Get audience from knowledge base if processed
                file_audience = None
                if is_processed:
                    # Check both filename and original name (without timestamp)
                    file_audience = file_audiences.get(filename)
                    if not file_audience and '_' in filename:
                        parts = filename.split('_', 2)
                        if len(parts) >= 3 and parts[0].isdigit() and len(parts[0]) == 8:
                            original_name = '_'.join(parts[2:])
                            file_audience = file_audiences.get(original_name)
                
                files.append({
                    'filename': filename,
                    'size': os.path.getsize(filepath),
                    'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                    'processed': is_processed,
                    'audience': file_audience
                })
    
    # Sort files by modified date (newest first)
    files.sort(key=lambda x: x['modified'], reverse=True)
    
    return jsonify({'files': files})

@app.route('/api/files/<filename>', methods=['DELETE'])
@login_required
def delete_file(filename):
    """Delete an uploaded file"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'success': True, 'message': 'File deleted'})
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/files/clear-all', methods=['DELETE'])
@login_required
def clear_all_files():
    """Delete all uploaded files"""
    try:
        upload_folder = app.config['UPLOAD_FOLDER']
        deleted_count = 0
        
        # Get all files in upload folder
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                filepath = os.path.join(upload_folder, filename)
                # Only delete files (not directories) and only allowed file types
                if os.path.isfile(filepath) and allowed_file(filename):
                    os.remove(filepath)
                    deleted_count += 1
        
        return jsonify({
            'success': True, 
            'message': f'Deleted {deleted_count} file(s)',
            'deleted_count': deleted_count
        })
    except Exception as e:
        return jsonify({'error': f'Failed to clear files: {str(e)}'}), 500

# Outlook integration removed - using .eml file upload instead

@app.route('/api/googledocs/ingest', methods=['POST'])
def ingest_google_doc():
    """Ingest a Google Doc into the knowledge base"""
    if not GOOGLE_DOCS_AVAILABLE:
        return jsonify({'error': 'Google Docs connector not available'}), 500
    
    try:
        data = request.json
        document_id = data.get('document_id', '').strip()
        credentials_file = data.get('credentials_file', 'credentials.json')
        token_file = data.get('token_file', 'token.pickle')
        
        if not document_id:
            return jsonify({'error': 'document_id is required'}), 400
        
        # Extract document ID from URL if full URL provided
        if 'docs.google.com' in document_id:
            # Extract ID from URL: docs.google.com/document/d/{ID}/edit
            import re
            match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', document_id)
            if match:
                document_id = match.group(1)
            else:
                return jsonify({'error': 'Could not extract document ID from URL'}), 400
        
        # Initialize connector and authenticate
        connector = GoogleDocsConnector()
        connector.authenticate(credentials_file=credentials_file, token_file=token_file)
        
        # Fetch document
        doc_data = connector.get_document(document_id)
        
        # Get audience label
        audience = data.get('audience')  # 'sales_reps', 'customers', 'internal', or None
        
        # Process and add to knowledge base
        processor = DataProcessor()
        documents_added = processor.process_google_doc(doc_data, audience=audience)
        
        return jsonify({
            'success': True,
            'message': f'Successfully ingested Google Doc: {doc_data["title"]}',
            'documents_added': documents_added,
            'title': doc_data['title']
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/gitlab/ingest', methods=['POST'])
def ingest_gitlab():
    """Ingest content from a GitLab repository"""
    if not GITLAB_AVAILABLE:
        return jsonify({'error': 'GitLab connector not available'}), 500
    
    try:
        data = request.json
        project_id = data.get('project_id', '').strip()
        gitlab_url = data.get('gitlab_url', os.getenv('GITLAB_URL', 'https://gitlab.com'))
        access_token = data.get('access_token', os.getenv('GITLAB_ACCESS_TOKEN'))
        ref = data.get('ref', 'main')
        
        include_commits = data.get('include_commits', True)
        include_readmes = data.get('include_readmes', True)
        include_release_notes = data.get('include_release_notes', True)
        max_commits = data.get('max_commits', 100)
        
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400
        
        if not access_token:
            return jsonify({'error': 'access_token is required (set GITLAB_ACCESS_TOKEN or pass in request)'}), 400
        
        # Initialize connector
        connector = GitLabConnector(gitlab_url=gitlab_url, access_token=access_token)
        
        # Get project info
        project = connector.get_project(project_id)
        project_name = project.get('name', project_id)
        
        # Ingest content
        documents = connector.ingest_project_content(
            project_id=project_id,
            ref=ref,
            include_commits=include_commits,
            include_readmes=include_readmes,
            include_release_notes=include_release_notes,
            max_commits=max_commits
        )
        
        # Get audience label
        audience = data.get('audience')  # 'sales_reps', 'customers', 'internal', or None
        
        # Process and add to knowledge base
        processor = DataProcessor()
        documents_added = processor.process_gitlab_documents(documents, audience=audience)
        
        return jsonify({
            'success': True,
            'message': f'Successfully ingested GitLab project: {project_name}',
            'documents_added': documents_added,
            'project_name': project_name,
            'sources': {
                'commits': sum(1 for d in documents if d['metadata'].get('source') == 'gitlab_commits'),
                'readmes': sum(1 for d in documents if d['metadata'].get('source') == 'gitlab_readme'),
                'release_notes': sum(1 for d in documents if d['metadata'].get('source') == 'gitlab_release_notes')
            }
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/googledocs/status', methods=['GET'])
def google_docs_status():
    """Check if Google Docs connector is available"""
    return jsonify({
        'available': GOOGLE_DOCS_AVAILABLE,
        'message': 'Google Docs connector is available' if GOOGLE_DOCS_AVAILABLE else 'Google Docs connector not available'
    })

@app.route('/api/gitlab/status', methods=['GET'])
def gitlab_status():
    """Check if GitLab connector is available"""
    return jsonify({
        'available': GITLAB_AVAILABLE,
        'has_token': bool(os.getenv('GITLAB_ACCESS_TOKEN')),
        'message': 'GitLab connector is available' if GITLAB_AVAILABLE else 'GitLab connector not available'
    })

@app.route('/sms', methods=['POST'])
def sms_reply():
    """Handle incoming SMS messages from Twilio"""
    # Get the message body and sender number
    incoming_msg = request.values.get('Body', '').strip()
    sender_phone = request.values.get('From', '')
    
    # Log the incoming message
    print(f"Received SMS from {sender_phone}: {incoming_msg}")
    
    # Get or initialize conversation history for this phone number
    if sender_phone not in twilio_conversations:
        twilio_conversations[sender_phone] = []
    
    conversation_history = twilio_conversations[sender_phone]
    
    # Add user message to history
    conversation_history.append({
        'role': 'user',
        'content': incoming_msg,
        'timestamp': datetime.now().isoformat()
    })
    
    # Generate response using the chatbot
    try:
        chatbot = ChatbotAgent()
        response_text, sources = chatbot.get_response_with_sources(
            incoming_msg, 
            conversation_history=conversation_history
        )
        
        # Add assistant response to history
        conversation_history.append({
            'role': 'assistant',
            'content': response_text,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep conversation history manageable (last 20 messages)
        if len(conversation_history) > 20:
            twilio_conversations[sender_phone] = conversation_history[-20:]
        
    except Exception as e:
        print(f"Error generating response: {e}")
        import traceback
        traceback.print_exc()
        response_text = "I apologize, but I encountered an error processing your request. Please try again or contact support directly."
    
    # Create TwiML response
    resp = MessagingResponse()
    resp.message(response_text)
    
    return Response(str(resp), mimetype='text/xml')

@app.route('/api/twilio/status', methods=['GET'])
def twilio_status():
    """Get Twilio integration status"""
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    phone_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    is_configured = bool(account_sid and auth_token and phone_number)
    
    return jsonify({
        'configured': is_configured,
        'phone_number': phone_number if is_configured else None,
        'active_conversations': len(twilio_conversations),
        'total_messages': sum(len(conv) for conv in twilio_conversations.values())
    })

@app.route('/api/twilio/conversations', methods=['GET'])
def list_twilio_conversations():
    """List all active Twilio conversations"""
    conversations = []
    for phone_number, history in twilio_conversations.items():
        conversations.append({
            'phone_number': phone_number,
            'message_count': len(history),
            'last_message': history[-1]['timestamp'] if history else None
        })
    
    return jsonify({'conversations': conversations})

@app.route('/api/twilio/conversations/<phone_number>', methods=['GET'])
def get_twilio_conversation(phone_number):
    """Get conversation history for a specific phone number"""
    # URL decode the phone number
    from urllib.parse import unquote
    phone_number = unquote(phone_number)
    
    if phone_number in twilio_conversations:
        return jsonify({
            'phone_number': phone_number,
            'messages': twilio_conversations[phone_number]
        })
    else:
        return jsonify({'error': 'Conversation not found'}), 404

@app.route('/api/twilio/conversations/<phone_number>', methods=['DELETE'])
def clear_twilio_conversation(phone_number):
    """Clear conversation history for a specific phone number"""
    from urllib.parse import unquote
    phone_number = unquote(phone_number)
    
    if phone_number in twilio_conversations:
        del twilio_conversations[phone_number]
        return jsonify({'status': 'success'})
    else:
        return jsonify({'error': 'Conversation not found'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    # Use debug=False in production (set via environment variable)
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

