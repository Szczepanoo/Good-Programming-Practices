from .database import SessionLocal, init_db
from .models import User
import bcrypt

init_db()

db = SessionLocal()
password = "admin123"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
new_user = User(username="admin", hashed_password=hashed.decode('utf-8'), roles="ROLE_USER,ROLE_ADMIN")
db.add(new_user)
db.commit()
db.close()
