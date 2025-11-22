import firebase_admin
from firebase_admin import credentials, firestore, auth
from app.config.settings import settings

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.GoogleServiceAccount)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

