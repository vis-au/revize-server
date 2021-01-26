from flask import Flask, render_template, session, copy_current_request_context
from flask_socketio import SocketIO, emit, disconnect
from threading import Lock

# https://medium.com/swlh/implement-a-websocket-using-flask-and-socket-io-python-76afa5bbeae1
# https://socket.io/get-started/chat/

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socket_ = SocketIO(app, cors_allowed_origins="*")

current_spec_version = 0
current_spec = {}

queue_of_clients = []
active_client_index = -1


@app.route("/")
def index():
  return render_template("index.html")


@socket_.on("register", namespace="/test")
def register(message):
  global queue_of_clients
  print("connected")
  client_id = message["id"]
  queue_of_clients += [client_id]

  emit("broadcast_spec", { "spec": current_spec, "version": current_spec_version })


@socket_.on("update_queue", namespace="/test")
def update_queue(message):
  global queue_of_clients

  if message["queue"] is None:
    return

  queue_of_clients = message["queue"]


@socket_.on("get_next", namespace="/test")
def get_next(message):

  this_client_id = queue_of_clients.index(message["source"])

  if this_client_id == len(queue_of_clients):
    return

  next_client_id = queue_of_clients[this_client_id + 1]

  print("forwarding data to next in queue...")
  emit("send_spec", { "spec": current_spec, "version": current_spec_version, "source": message["source"], "target": next_client_id }, broadcast=True)


@socket_.on("get_previous", namespace="/test")
def get_previous(message):

  this_client_id = queue_of_clients.index(message["source"])

  if this_client_id == 0:
    return

  previous_client_id = queue_of_clients[this_client_id - 1]

  print("forwarding data to previous in queue...")
  emit("send_spec", { "spec": current_spec, "version": current_spec_version, "source": message["source"], "target": previous_client_id }, broadcast=True)


@socket_.on("update_spec", namespace="/test")
def update_spec(message):
  global current_spec, current_spec_version

  if message['version'] != current_spec_version:
    return

  current_spec_version += 1
  current_spec = message['spec']
  print("received new spec")

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
