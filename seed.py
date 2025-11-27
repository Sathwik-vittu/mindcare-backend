from app import app, db, User, Medication, Appointment, ForumPost, ForumReply, bcrypt
from datetime import datetime, timedelta
import random

def seed_database():
    with app.app_context():
        print("🗑️  Clearing existing data...")
        # Clear existing data
        ForumReply.query.delete()
        ForumPost.query.delete()
        Appointment.query.delete()
        Medication.query.delete()
        User.query.delete()
        db.session.commit()
        
        print("👤 Creating users...")
        # Create sample users
        users = []
        user_data = [
            {"username": "john_doe", "email": "john@example.com", "password": "password123", "full_name": "John Doe", "gender": "male", "phone": "+1-555-0101"},
            {"username": "jane_smith", "email": "jane@example.com", "password": "password123", "full_name": "Jane Smith", "gender": "female", "phone": "+1-555-0102"},
            {"username": "mike_wilson", "email": "mike@example.com", "password": "password123", "full_name": "Mike Wilson", "gender": "male", "phone": "+1-555-0103"},
            {"username": "sarah_jones", "email": "sarah@example.com", "password": "password123", "full_name": "Sarah Jones", "gender": "female", "phone": "+1-555-0104"},
            {"username": "alex_brown", "email": "alex@example.com", "password": "password123", "full_name": "Alex Brown", "gender": "non-binary", "phone": "+1-555-0105"},
        ]
        
        for data in user_data:
            user = User(
                username=data["username"],
                email=data["email"],
                password=bcrypt.generate_password_hash(data["password"]).decode('utf-8'),
                full_name=data["full_name"],
                gender=data["gender"],
                phone=data["phone"],
                date_of_birth=datetime(1990 + random.randint(0, 15), random.randint(1, 12), random.randint(1, 28)).date(),
                emergency_contact=f"Emergency Contact - {data['phone']}",
                medical_history="No significant medical history",
                psychiatric_history="Seeking support for anxiety and stress management"
            )
            db.session.add(user)
            users.append(user)
        
        db.session.commit()
        print(f"   ✅ Created {len(users)} users")
        
        print("💊 Creating medications...")
        # Create sample medications
        medications_data = [
            {"name": "Sertraline", "dosage": "50mg", "frequency": "Once daily", "time_to_take": "8:00 AM", "doctor_name": "Dr. Smith"},
            {"name": "Escitalopram", "dosage": "10mg", "frequency": "Once daily", "time_to_take": "9:00 AM", "doctor_name": "Dr. Johnson"},
            {"name": "Buspirone", "dosage": "15mg", "frequency": "Twice daily", "time_to_take": "8:00 AM, 8:00 PM", "doctor_name": "Dr. Williams"},
            {"name": "Hydroxyzine", "dosage": "25mg", "frequency": "As needed", "time_to_take": "Before bed", "doctor_name": "Dr. Davis"},
            {"name": "Melatonin", "dosage": "5mg", "frequency": "Once daily", "time_to_take": "10:00 PM", "doctor_name": "Dr. Miller"},
        ]
        
        med_count = 0
        for user in users[:3]:
            for med_data in random.sample(medications_data, random.randint(1, 3)):
                medication = Medication(
                    user_id=user.id,
                    name=med_data["name"],
                    dosage=med_data["dosage"],
                    frequency=med_data["frequency"],
                    time_to_take=med_data["time_to_take"],
                    doctor_name=med_data["doctor_name"],
                    doctor_contact=f"+1-555-{random.randint(1000, 9999)}",
                    start_date=datetime.now().date() - timedelta(days=random.randint(30, 180)),
                    refill_date=datetime.now().date() + timedelta(days=random.randint(1, 30)),
                    notes=f"Take with food. Monitor for side effects.",
                    reminder_enabled=True
                )
                db.session.add(medication)
                med_count += 1
        
        db.session.commit()
        print(f"   ✅ Created {med_count} medications")
        
        print("📅 Creating appointments...")
        # Create sample appointments
        appointment_types = [
            "Therapy Session",
            "Psychiatrist Consultation",
            "Follow-up Appointment",
            "Medication Review",
            "Group Therapy",
            "Initial Assessment",
        ]
        
        doctors = ["Dr. Smith", "Dr. Johnson", "Dr. Williams", "Dr. Davis", "Dr. Miller"]
        locations = ["Mental Health Clinic", "Community Hospital", "Private Practice", "Wellness Center", "Online/Telehealth"]
        
        apt_count = 0
        for user in users:
            # Past appointments
            for i in range(random.randint(1, 3)):
                apt = Appointment(
                    user_id=user.id,
                    title=random.choice(appointment_types),
                    description="Regular scheduled appointment",
                    doctor_name=random.choice(doctors),
                    location=random.choice(locations),
                    appointment_date=datetime.now() - timedelta(days=random.randint(1, 60)),
                    reminder_time=60,
                    status="completed"
                )
                db.session.add(apt)
                apt_count += 1
            
            # Upcoming appointments
            for i in range(random.randint(1, 2)):
                apt = Appointment(
                    user_id=user.id,
                    title=random.choice(appointment_types),
                    description="Upcoming scheduled appointment",
                    doctor_name=random.choice(doctors),
                    location=random.choice(locations),
                    appointment_date=datetime.now() + timedelta(days=random.randint(1, 30), hours=random.randint(9, 17)),
                    reminder_time=60,
                    status="scheduled"
                )
                db.session.add(apt)
                apt_count += 1
        
        db.session.commit()
        print(f"   ✅ Created {apt_count} appointments")
        
        print("💬 Creating forum posts...")
        # Create sample forum posts
        posts_data = [
            {
                "title": "Tips for managing anxiety during work",
                "content": "I've been struggling with anxiety at work lately. What strategies have helped you cope? I find deep breathing helps but looking for more techniques.",
                "category": "anxiety"
            },
            {
                "title": "Medication side effects - seeking advice",
                "content": "Started a new medication last week and experiencing some tiredness. Did anyone else experience this? How long did it take to adjust?",
                "category": "general"
            },
            {
                "title": "Celebrating 6 months of therapy!",
                "content": "Just wanted to share that I've completed 6 months of consistent therapy and I'm seeing real progress. Don't give up, it gets better!",
                "category": "success"
            },
            {
                "title": "How do you explain mental health to family?",
                "content": "My family doesn't really understand what I'm going through. How have you approached these conversations with loved ones?",
                "category": "support"
            },
            {
                "title": "Mindfulness apps recommendations",
                "content": "Looking for good mindfulness and meditation apps. What do you all use? Free or paid, any suggestions welcome!",
                "category": "resources"
            },
            {
                "title": "Dealing with low motivation days",
                "content": "Some days I just can't find the motivation to do anything. How do you push through those really tough days?",
                "category": "depression"
            },
            {
                "title": "First time posting - nervous but hopeful",
                "content": "Hi everyone, this is my first time reaching out in a community like this. I've been dealing with anxiety for years and finally decided to seek help.",
                "category": "general"
            },
            {
                "title": "Exercise and mental health connection",
                "content": "I've noticed that regular exercise really helps my mood. Does anyone have a workout routine that works well for managing mental health?",
                "category": "resources"
            },
        ]
        
        posts = []
        for i, post_data in enumerate(posts_data):
            post = ForumPost(
                user_id=users[i % len(users)].id,
                title=post_data["title"],
                content=post_data["content"],
                category=post_data["category"],
                is_moderated=True,
                created_at=datetime.now() - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))
            )
            db.session.add(post)
            posts.append(post)
        
        db.session.commit()
        print(f"   ✅ Created {len(posts)} forum posts")
        
        print("💭 Creating forum replies...")
        # Create sample replies
        reply_contents = [
            "Thank you for sharing this! I can really relate to what you're going through.",
            "This is really helpful advice. I'll try implementing this.",
            "You're doing great! Keep up the good work.",
            "I've experienced something similar. What helped me was taking things one day at a time.",
            "Sending positive thoughts your way! You're not alone in this.",
            "This community is so supportive. Thank you all!",
            "I recommend talking to your doctor about this. They might have some suggestions.",
            "Deep breathing and journaling have been game changers for me.",
            "It's okay to have bad days. What matters is that you keep trying.",
            "Have you tried cognitive behavioral therapy techniques? They really helped me.",
        ]
        
        reply_count = 0
        for post in posts:
            num_replies = random.randint(1, 5)
            for _ in range(num_replies):
                reply = ForumReply(
                    post_id=post.id,
                    user_id=random.choice(users).id,
                    content=random.choice(reply_contents),
                    is_moderated=True,
                    created_at=post.created_at + timedelta(hours=random.randint(1, 72))
                )
                db.session.add(reply)
                reply_count += 1
        
        db.session.commit()
        print(f"   ✅ Created {reply_count} forum replies")
        
        print("\n" + "="*50)
        print("🎉 Database seeded successfully!")
        print("="*50)
        print("\n📧 Test Accounts:")
        print("-"*50)
        for user in user_data:
            print(f"   Email: {user['email']}")
            print(f"   Password: {user['password']}")
            print("-"*50)

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🌱 Mental Health App - Database Seeder")
    print("="*50 + "\n")
    
    # Create tables first
    with app.app_context():
        print("📦 Creating database tables...")
        db.create_all()
        print("   ✅ Tables created!\n")
    
    seed_database()
