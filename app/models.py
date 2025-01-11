from app import db
from datetime import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    otp_code = db.Column(db.String(4), nullable=True)


class Object(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    limit = db.Column(db.Integer, nullable=False)
    solved_count = db.Column(db.Integer, default=0, nullable=False)


class Solved(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    object_id = db.Column(db.Integer, db.ForeignKey('object.id'), nullable=False)
    date_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('solved_entries', lazy=True))
    object = db.relationship('Object', backref=db.backref('solved_entries', lazy=True))
