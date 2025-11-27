
from app import app, db, User, Medication, Appointment, ForumPost, ForumReply, bcrypt
from datetime import datetime, timedelta
import random

def seed_specific_user():
    with app.app_context():
        print("👤 Creating specific user...")
        
        email = "anshc022@gmail.com"
        password = "111111"
        username = "anshc022"
        full_name = "Ansh C."
        
        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"User {email} already exists. Updating password...")
            existing_user.password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = existing_user
        else:
            user = User(
                username=username,
                email=email,
                password=bcrypt.generate_password_hash(password).decode('utf-8'),
                full_name=full_name,
                gender="Prefer not to say",
                phone="+1-555-0199",
                date_of_birth=datetime(1995, 5, 15).date(),
                emergency_contact="Emergency Contact - +1-555-0199",
                medical_history="None",
                psychiatric_history="None"
            )
            db.session.add(user)
        
        db.session.commit()
        print(f"   ✅ User {email} ready")
        
        # Add medications
        print("💊 Adding medications...")
        medications_data = [
            {"name": "Vitamin D", "dosage": "1000IU", "frequency": "Once daily", "time_to_take": "Morning", "doctor_name": "Dr. Wellness"},
            {"name": "Omega-3", "dosage": "1000mg", "frequency": "Once daily", "time_to_take": "Lunch", "doctor_name": "Dr. Wellness"},
        ]
        
        for med_data in medications_data:
            # Check if medication already exists for this user to avoid duplicates on re-run
            existing_med = Medication.query.filter_by(user_id=user.id, name=med_data["name"]).first()
            if not existing_med:
                medication = Medication(
                    user_id=user.id,
                    name=med_data["name"],
                    dosage=med_data["dosage"],
                    frequency=med_data["frequency"],
                    time_to_take=med_data["time_to_take"],
                    doctor_name=med_data["doctor_name"],
                    doctor_contact="+1-555-0000",
                    start_date=datetime.now().date() - timedelta(days=30),
                    refill_date=datetime.now().date() + timedelta(days=random.randint(2, 10)), # Soon to trigger alert
                    notes="Take with food",
                    reminder_enabled=True
                )
                db.session.add(medication)
        
        # Add appointments
        print("📅 Adding appointments...")
        appointments_data = [
            {
                "title": "Wellness Checkup",
                "doctor_name": "Dr. Smith",
                "date": datetime.now() + timedelta(days=2, hours=4),
                "status": "scheduled"
            },
            {
                "title": "Therapy Session",
                "doctor_name": "Dr. Johnson",
                "date": datetime.now() + timedelta(days=5, hours=2),
                "status": "scheduled"
            }
        ]
        
        for apt_data in appointments_data:
             # Simple check to avoid exact duplicates on re-run
            existing_apt = Appointment.query.filter_by(user_id=user.id, title=apt_data["title"], appointment_date=apt_data["date"]).first()
            if not existing_apt:
                apt = Appointment(
                    user_id=user.id,
                    title=apt_data["title"],
                    description="Regular checkup",
                    doctor_name=apt_data["doctor_name"],
                    location="Clinic",
                    appointment_date=apt_data["date"],
                    reminder_time=60,
                    status=apt_data["status"]
                )
                db.session.add(apt)

        db.session.commit()
        print("   ✅ Data seeded successfully!")

if __name__ == "__main__":
    seed_specific_user()
