from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os

app = Flask(__name__)


def _apply_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response


@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        response = make_response('', 204)
        return _apply_cors(response)
    return None


@app.after_request
def add_cors_headers(response):
    return _apply_cors(response)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mental-health-app-secret-key-2024')

# Read database URL from environment (for Render Postgres)
db_url = os.environ.get('DATABASE_URL')

# Render Postgres often uses "postgres://" – SQLAlchemy prefers "postgresql://"
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Fallback to local SQLite if no DATABASE_URL is set (for local dev)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///mental_health.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    emergency_contact = db.Column(db.String(150))
    medical_history = db.Column(db.Text)
    psychiatric_history = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    medications = db.relationship('Medication', backref='user', lazy=True)
    appointments = db.relationship('Appointment', backref='user', lazy=True)
    forum_posts = db.relationship('ForumPost', backref='author', lazy=True)
    replies = db.relationship('ForumReply', backref='author', lazy=True)

class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50))
    frequency = db.Column(db.String(100))
    time_to_take = db.Column(db.String(50))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    refill_date = db.Column(db.Date)
    doctor_name = db.Column(db.String(100))
    doctor_contact = db.Column(db.String(100))
    notes = db.Column(db.Text)
    reminder_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    doctor_name = db.Column(db.String(100))
    location = db.Column(db.String(200))
    appointment_date = db.Column(db.DateTime, nullable=False)
    reminder_time = db.Column(db.Integer, default=60)  # minutes before
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='general')
    is_moderated = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    replies = db.relationship('ForumReply', backref='post', lazy=True, order_by='ForumReply.created_at')

class ForumReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_moderated = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Simple content moderation (simulating LLM API)
def moderate_content(content):
    """Simple content moderation - checks for harmful keywords"""
    harmful_words = ['suicide', 'kill', 'harm', 'hurt myself', 'end my life']
    content_lower = content.lower()
    for word in harmful_words:
        if word in content_lower:
            return False, "Content flagged for review. Please reach out to a mental health professional if you're in crisis."
    return True, "Content approved"

# Auth Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 400
    
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password,
        full_name=data.get('full_name', '')
    )
    
    db.session.add(user)
    db.session.commit()
    
    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        'message': 'Registration successful',
        'access_token': access_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name
        }
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and bcrypt.check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name
            }
        })
    
    return jsonify({'error': 'Invalid email or password'}), 401

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': user.full_name,
        'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
        'gender': user.gender,
        'phone': user.phone,
        'emergency_contact': user.emergency_contact,
        'medical_history': user.medical_history,
        'psychiatric_history': user.psychiatric_history
    })

# Profile Routes
@app.route('/api/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    data = request.get_json()
    
    user.full_name = data.get('full_name', user.full_name)
    user.phone = data.get('phone', user.phone)
    user.gender = data.get('gender', user.gender)
    user.emergency_contact = data.get('emergency_contact', user.emergency_contact)
    user.medical_history = data.get('medical_history', user.medical_history)
    user.psychiatric_history = data.get('psychiatric_history', user.psychiatric_history)
    
    if data.get('date_of_birth'):
        user.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
    
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'})

# Medication Routes
@app.route('/api/medications', methods=['GET'])
@jwt_required()
def get_medications():
    user_id = int(get_jwt_identity())
    medications = Medication.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'dosage': m.dosage,
        'frequency': m.frequency,
        'time_to_take': m.time_to_take,
        'start_date': m.start_date.isoformat() if m.start_date else None,
        'end_date': m.end_date.isoformat() if m.end_date else None,
        'refill_date': m.refill_date.isoformat() if m.refill_date else None,
        'doctor_name': m.doctor_name,
        'doctor_contact': m.doctor_contact,
        'notes': m.notes,
        'reminder_enabled': m.reminder_enabled
    } for m in medications])

@app.route('/api/medications', methods=['POST'])
@jwt_required()
def create_medication():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    medication = Medication(
        user_id=user_id,
        name=data['name'],
        dosage=data.get('dosage'),
        frequency=data.get('frequency'),
        time_to_take=data.get('time_to_take'),
        doctor_name=data.get('doctor_name'),
        doctor_contact=data.get('doctor_contact'),
        notes=data.get('notes'),
        reminder_enabled=data.get('reminder_enabled', True)
    )
    
    if data.get('start_date'):
        medication.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    if data.get('end_date'):
        medication.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    if data.get('refill_date'):
        medication.refill_date = datetime.strptime(data['refill_date'], '%Y-%m-%d').date()
    
    db.session.add(medication)
    db.session.commit()
    return jsonify({'message': 'Medication added successfully', 'id': medication.id}), 201

@app.route('/api/medications/<int:id>', methods=['PUT'])
@jwt_required()
def update_medication(id):
    user_id = int(get_jwt_identity())
    medication = Medication.query.filter_by(id=id, user_id=user_id).first()
    
    if not medication:
        return jsonify({'error': 'Medication not found'}), 404
    
    data = request.get_json()
    medication.name = data.get('name', medication.name)
    medication.dosage = data.get('dosage', medication.dosage)
    medication.frequency = data.get('frequency', medication.frequency)
    medication.time_to_take = data.get('time_to_take', medication.time_to_take)
    medication.doctor_name = data.get('doctor_name', medication.doctor_name)
    medication.doctor_contact = data.get('doctor_contact', medication.doctor_contact)
    medication.notes = data.get('notes', medication.notes)
    medication.reminder_enabled = data.get('reminder_enabled', medication.reminder_enabled)
    
    if data.get('start_date'):
        medication.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    if data.get('end_date'):
        medication.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    if data.get('refill_date'):
        medication.refill_date = datetime.strptime(data['refill_date'], '%Y-%m-%d').date()
    
    db.session.commit()
    return jsonify({'message': 'Medication updated successfully'})

@app.route('/api/medications/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_medication(id):
    user_id = int(get_jwt_identity())
    medication = Medication.query.filter_by(id=id, user_id=user_id).first()
    
    if not medication:
        return jsonify({'error': 'Medication not found'}), 404
    
    db.session.delete(medication)
    db.session.commit()
    return jsonify({'message': 'Medication deleted successfully'})

# Appointment Routes
@app.route('/api/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    user_id = int(get_jwt_identity())
    appointments = Appointment.query.filter_by(user_id=user_id).order_by(Appointment.appointment_date).all()
    return jsonify([{
        'id': a.id,
        'title': a.title,
        'description': a.description,
        'doctor_name': a.doctor_name,
        'location': a.location,
        'appointment_date': a.appointment_date.isoformat(),
        'reminder_time': a.reminder_time,
        'status': a.status
    } for a in appointments])

@app.route('/api/appointments', methods=['POST'])
@jwt_required()
def create_appointment():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    appointment = Appointment(
        user_id=user_id,
        title=data['title'],
        description=data.get('description'),
        doctor_name=data.get('doctor_name'),
        location=data.get('location'),
        appointment_date=datetime.fromisoformat(data['appointment_date']),
        reminder_time=data.get('reminder_time', 60),
        status=data.get('status', 'scheduled')
    )
    
    db.session.add(appointment)
    db.session.commit()
    return jsonify({'message': 'Appointment created successfully', 'id': appointment.id}), 201

@app.route('/api/appointments/<int:id>', methods=['PUT'])
@jwt_required()
def update_appointment(id):
    user_id = int(get_jwt_identity())
    appointment = Appointment.query.filter_by(id=id, user_id=user_id).first()
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    data = request.get_json()
    appointment.title = data.get('title', appointment.title)
    appointment.description = data.get('description', appointment.description)
    appointment.doctor_name = data.get('doctor_name', appointment.doctor_name)
    appointment.location = data.get('location', appointment.location)
    appointment.reminder_time = data.get('reminder_time', appointment.reminder_time)
    appointment.status = data.get('status', appointment.status)
    
    if data.get('appointment_date'):
        appointment.appointment_date = datetime.fromisoformat(data['appointment_date'])
    
    db.session.commit()
    return jsonify({'message': 'Appointment updated successfully'})

@app.route('/api/appointments/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_appointment(id):
    user_id = int(get_jwt_identity())
    appointment = Appointment.query.filter_by(id=id, user_id=user_id).first()
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    db.session.delete(appointment)
    db.session.commit()
    return jsonify({'message': 'Appointment deleted successfully'})

# Forum Routes
@app.route('/api/forum/posts', methods=['GET'])
@jwt_required()
def get_forum_posts():
    category = request.args.get('category')
    query = ForumPost.query.filter_by(is_moderated=True)
    
    if category and category != 'all':
        query = query.filter_by(category=category)
    
    posts = query.order_by(ForumPost.created_at.desc()).all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'content': p.content,
        'category': p.category,
        'author': {
            'id': p.author.id,
            'username': p.author.username
        },
        'reply_count': len([r for r in p.replies if r.is_moderated]),
        'created_at': p.created_at.isoformat(),
        'updated_at': p.updated_at.isoformat()
    } for p in posts])

@app.route('/api/forum/posts/<int:id>', methods=['GET'])
@jwt_required()
def get_forum_post(id):
    post = ForumPost.query.get(id)
    
    if not post or not post.is_moderated:
        return jsonify({'error': 'Post not found'}), 404
    
    return jsonify({
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'category': post.category,
        'author': {
            'id': post.author.id,
            'username': post.author.username
        },
        'replies': [{
            'id': r.id,
            'content': r.content,
            'author': {
                'id': r.author.id,
                'username': r.author.username
            },
            'created_at': r.created_at.isoformat()
        } for r in post.replies if r.is_moderated],
        'created_at': post.created_at.isoformat(),
        'updated_at': post.updated_at.isoformat()
    })

@app.route('/api/forum/posts', methods=['POST'])
@jwt_required()
def create_forum_post():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    # Moderate content
    is_safe, message = moderate_content(data['content'])
    if not is_safe:
        return jsonify({'error': message}), 400
    
    is_safe, message = moderate_content(data['title'])
    if not is_safe:
        return jsonify({'error': message}), 400
    
    post = ForumPost(
        user_id=user_id,
        title=data['title'],
        content=data['content'],
        category=data.get('category', 'general'),
        is_moderated=True
    )
    
    db.session.add(post)
    db.session.commit()
    return jsonify({'message': 'Post created successfully', 'id': post.id}), 201

@app.route('/api/forum/posts/<int:post_id>/replies', methods=['POST'])
@jwt_required()
def create_forum_reply(post_id):
    user_id = int(get_jwt_identity())
    post = ForumPost.query.get(post_id)
    
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    data = request.get_json()
    
    # Moderate content
    is_safe, message = moderate_content(data['content'])
    if not is_safe:
        return jsonify({'error': message}), 400
    
    reply = ForumReply(
        post_id=post_id,
        user_id=user_id,
        content=data['content'],
        is_moderated=True
    )
    
    db.session.add(reply)
    db.session.commit()
    return jsonify({'message': 'Reply added successfully', 'id': reply.id}), 201

# Dashboard Stats
@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    user_id = int(get_jwt_identity())
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.query.filter(
        Appointment.user_id == user_id,
        Appointment.appointment_date >= datetime.now(),
        Appointment.status == 'scheduled'
    ).order_by(Appointment.appointment_date).limit(5).all()
    
    # Get active medications
    medications = Medication.query.filter_by(user_id=user_id).all()
    
    # Get medications needing refill soon (within 7 days)
    refill_soon = []
    for m in medications:
        if m.refill_date and (m.refill_date - datetime.now().date()).days <= 7:
            refill_soon.append(m)
    
    return jsonify({
        'total_medications': len(medications),
        'upcoming_appointments': [{
            'id': a.id,
            'title': a.title,
            'doctor_name': a.doctor_name,
            'appointment_date': a.appointment_date.isoformat()
        } for a in upcoming_appointments],
        'medications_needing_refill': [{
            'id': m.id,
            'name': m.name,
            'refill_date': m.refill_date.isoformat() if m.refill_date else None
        } for m in refill_soon]
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
