import re

from flask import Flask, request, jsonify, render_template
from flask_admin import Admin as FlaskAdmin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime, timedelta

from extensions import db
from models import Room, Admin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bingo_bot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
admin = FlaskAdmin(app, name='bingo_bot')
admin.add_view(ModelView(Room, db.session))
admin.add_view(ModelView(Admin, db.session, name='Admin', endpoint='admin_model_view'))

# Маршрут для отображения интерфейса
@app.route('/')
def index():
    rooms = Room.query.all()
    return render_template('index.html', rooms=rooms)


def extract_matrix_id(input_string):
    match = re.search(r"[!#]?([a-zA-Z0-9_-]+:matrix.org)", input_string)
    if match:
        return match.group(0)
    return None

# Маршрут для добавления новой комнаты
@app.route('/add_room', methods=['POST'])
def add_room():
    data = request.json
    title = data.get('title')
    room_id = data.get('room_id').lstrip('#')  # Удалить #, если он есть
    room_id = extract_matrix_id(room_id)
    payer_nickname = data.get('payer_nickname')
    admins = data.get('admins', [])
    days = data.get('days', 0)
    minutes = data.get('minutes', 0)

    subscription_end = datetime.now() + timedelta(days=days, minutes=minutes)
    new_room = Room(room_id=room_id, title=title, payer_nickname=payer_nickname, subscription_end=subscription_end)

    db.session.add(new_room)
    db.session.commit()

    # Добавление администраторов в базу данных
    for adm in admins:
        new_admin = Admin(room_id=room_id, admin_account=adm)
        db.session.add(new_admin)
        new_room.admins.append(new_admin)

    db.session.commit()
    return jsonify(success=True, message="Комната добавлена успешно.")

# Маршрут для продления подписки
@app.route('/extend_subscription/<room_id>', methods=['POST'])
def extend_subscription(room_id):
    room = db.session.query(Room).filter_by(room_id=room_id).first()
    print(room)
    if not room:
        return jsonify(success=False, message="Комната не найдена."), 404

    data = request.json
    days = data.get('days', 0)
    minutes = data.get('minutes', 0)
    additional_time = timedelta(days=days, minutes=minutes)

    if room.subscription_end:
        room.subscription_end += additional_time
    else:
        room.subscription_end = datetime.now() + additional_time

    db.session.commit()
    return jsonify(success=True, message="Подписка продлена успешно.")

# Маршрут для обновления информации о комнате
@app.route('/update_room/<room_id>', methods=['POST'])
def update_room(room_id):
    room = db.session.query(Room).filter_by(room_id=room_id).first()
    if not room:
        return jsonify(success=False, message="Комната не найдена."), 404

    data = request.json
    room.title = data.get('title', room.title)
    room.payer_nickname = data.get('payer_nickname', room.payer_nickname)

    # Обновление администраторов
    Admin.query.filter_by(room_id=room.id).delete()
    for admin in data.get('admins', []):
        new_admin = Admin(room_id=room.id, admin_account=admin)
        db.session.add(new_admin)

    db.session.commit()
    return jsonify(success=True, message="Информация о комнате обновлена успешно.")

# Маршрут для удаления комнаты
@app.route('/delete_room/<room_id>', methods=['DELETE'])
def delete_room(room_id):
    room = db.session.query(Room).filter_by(room_id=room_id).first()
    if not room:
        return jsonify(success=False, message="Комната не найдена."), 404

    Admin.query.filter_by(room_id=room.id).delete()
    db.session.delete(room)
    db.session.commit()
    return jsonify(success=True, message="Комната удалена успешно.")

# Маршрут для получения списка администраторов для комнаты
@app.route('/get_admins/<room_id>', methods=['GET'])
def get_admins(room_id):
    room = db.session.query(Room).filter_by(room_id=room_id).first()
    if not room:
        return jsonify(success=False, message="Комната не найдена."), 404

    admins = [admin.admin_account for admin in room.admins]
    return jsonify(success=True, admins=admins)

# Маршрут для получения статуса подписки для комнаты
@app.route('/get_subscription/<room_id>', methods=['GET'])
def get_subscription(room_id):
    room = db.session.query(Room).filter_by(room_id=room_id).first()
    if not room:
        return jsonify(success=False, message="Комната не найдена."), 404

    subscription_end = room.subscription_end.isoformat() if room.subscription_end else None
    return jsonify(success=True, subscription_end=subscription_end)

# Запуск приложения и создание таблиц базы данных при запуске
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
