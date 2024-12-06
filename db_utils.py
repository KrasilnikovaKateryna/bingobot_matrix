import traceback
from datetime import datetime, timedelta

from models import Room
from extensions import db

def get_admins(room_id):
    admins = []
    try:
        room = db.session.query(Room).filter_by(room_id=room_id).first()
        print(room)
        for db_admin in room.admins:
            if db_admin.admin_account not in admins:
                admins.append(db_admin.admin_account)
    except Exception as e:
        print(f"Error: {e}")
        print(traceback.format_exc())

    return admins

def get_rooms():
    db_rec_rooms = db.session.query(Room).all()
    rooms_id = []
    for room in db_rec_rooms:
        try:
            room_id = room.room_id
            if room_id not in rooms_id:
                rooms_id.append(room_id)
        except:
            print(traceback.format_exc())


    return rooms_id


def get_subscription(room_id):
    print(room_id)
    room = db.session.query(Room).filter_by(room_id=room_id).first()

    return room.subscription_end
