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
  client_id = message["id"]
  print(client_id, "has connected. Sending latest version ...")
  queue_of_clients += [client_id]

  emit("broadcast_spec", { "spec": current_spec, "version": current_spec_version })


@socket_.on("update_queue", namespace="/test")
def update_queue(message):
  global queue_of_clients

  if message["queue"] is None:
    return

  queue_of_clients = message["queue"]


@socket_.on("request_queue", namespace="/test")
def request_queue(message):
  global queue_of_clients

  emit("send_queue", { "queue": queue_of_clients })


@socket_.on("get_next", namespace="/test")
def get_next(message):
  global current_spec, current_spec_version

  this_client_index = queue_of_clients.index(message["source"])

  if this_client_index == len(queue_of_clients) - 1:
    print("source client is last in queue. No next client available.")
    return

  next_client_id = queue_of_clients[this_client_index + 1]

  if message['version'] != current_spec_version:
    return

  current_spec_version += 1
  current_spec = message['spec']
  print("received new spec")

  print("forwarding data to next in queue with id", next_client_id, "...")
  emit("broadcast_spec", { "spec": current_spec, "version": current_spec_version })
  emit("send_spec", { "spec": current_spec, "version": current_spec_version, "source": message["source"], "target": next_client_id }, broadcast=True)


@socket_.on("get_previous", namespace="/test")
def get_previous(message):
  global current_spec, current_spec_version

  this_client_index = queue_of_clients.index(message["source"])

  if this_client_index == 0:
    print("source client is first in queue. No previous client available.")
    return

  if message['version'] != current_spec_version:
    return

  previous_client_id = queue_of_clients[this_client_index - 1]

  current_spec_version += 1
  current_spec = message['spec']
  print("received new spec")

  print("forwarding data to previous in queue with id", previous_client_id, "...")
  emit("broadcast_spec", { "spec": current_spec, "version": current_spec_version })
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
