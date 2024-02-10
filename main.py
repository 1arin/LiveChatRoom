from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin, login_user, LoginManager,login_required, logout_user, current_user
import bcrypt


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'
# add Database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self,email,password,name):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self,password):
        return bcrypt.checkpw(password.encode('utf-8'),self.password.encode('utf-8'))

with app.app_context():
    db.create_all()
# Secret Key
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app)

rooms = {}


@app.route("/")
def main():
    return render_template("main.html")

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    
    return code

@app.route("/joinroom", methods=["POST", "GET"])
def joinroom():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("joinroom.html", error="Please enter a name", code=code , name=name)
        
        if join != False and not code:
            return render_template("joinroom.html", error="Please enter a room code", code=code , name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("joinroom.html", error="Room does not exist.", code=code , name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    # run html file called "home.html"
    return render_template("joinroom.html")

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("joinroom"))

    return render_template("room.html", code=room, message=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@app.route('/contact')
def contact():
    return render_template('contact.html')

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room in rooms:
        return
    if room not in rooms:

        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined the room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

    send({"name": name, "message": "has lefted the room"}, to=room)
    print(f"{name} has left the room {room}")

@app.route("/register", methods=['GET','POST'])
def register():
    if request.method == 'POST':
        # handle request
        pass

    return render_template('register.html')

@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'POST':
        # handle request
        pass
    return render_template('login.html')

if __name__ == "__main__":
    socketio.run(app, debug=True)

    