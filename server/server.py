from flask import Flask, render_template, session, copy_current_request_context
from flask_socketio import SocketIO, emit, disconnect
from threading import Lock

# https://medium.com/swlh/implement-a-websocket-using-flask-and-socket-io-python-76afa5bbeae1
# https://socket.io/get-started/chat/

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socket_ = SocketIO(app)

current_spec_version = 0
current_spec = {}

@app.route("/")
def index():
  return render_template("index.html")

@socket_.on("register", namespace="/test")
def register(message):
  emit("broadcast_spec", { "spec": current_spec, "version": current_spec_version }, broadcast=True)


@socket_.on("update_spec", namespace="/test")
def update_spec(message):
  global current_spec, current_spec_version
  current_spec_version += 1
  current_spec = message.spec

  emit("broadcast_spec", { "spec": current_spec, "version": current_spec_version }, broadcast=True)


@socket_.on("disconnect_request", namespace="/test")
def disconnect_request():
  @copy_current_request_context
  def can_disconnect():
    disconnect()

  session["receive_count"] = session.get("receive_count", 0) + 1
  emit("my_response", {"data": "Disconnected!", "count": session["receive_count"]}, callback=can_disconnect)


if __name__ == "__main__":
  socket_.run(app, debug=True)