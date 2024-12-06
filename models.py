from sqlalchemy.orm import backref

from extensions import db

class Room(db.Model):
    __tablename__ = "room"
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    payer_nickname = db.Column(db.String(50), nullable=False)
    subscription_end = db.Column(db.DateTime, nullable=True)
    admins = db.relationship('Admin', backref=db.backref('admin', uselist=False))

    def __repr__(self):
        return f"<Room {self.title}, ID: {self.room_id}>"

class Admin(db.Model):
    __tablename__ = "admin"
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    admin_account = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<Admin {self.admin_account} for Room ID: {self.room_id}>"

