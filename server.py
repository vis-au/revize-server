from flask import Flask, render_template, session, copy_current_request_context, jsonify
from flask_socketio import SocketIO, emit, disconnect
from threading import Lock

# https://medium.com/swlh/implement-a-websocket-using-flask-and-socket-io-python-76afa5bbeae1
# https://socket.io/get-started/chat/

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socket_ = SocketIO(app, cors_allowed_origins="*")

current_spec = {
  "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
  "description": "A simple bar chart with embedded data.",
  "data": {
    "values": [
      {"a": "A", "b": 28}, {"a": "B", "b": 55}, {"a": "C", "b": 43},
      {"a": "D", "b": 91}, {"a": "E", "b": 81}, {"a": "F", "b": 53},
      {"a": "G", "b": 19}, {"a": "H", "b": 87}, {"a": "I", "b": 52}
    ]
  },
  "mark": "bar",
  "encoding": {
    "x": {"field": "a", "type": "nominal", "axis": {"labelAngle": 0}},
    "y": {"field": "b", "type": "quantitative"},
    "color": {
      "field": "a",
      "type": "nominal"
    }
  }
}

unused_ids = []
queue_of_clients = []


@app.route("/")
def index():
  return render_template("index.html")


# REGISTRATION #####################################################################################

@app.route('/add/<id>', methods=['GET'])
def add_id_to_pool(id):
  global unused_ids
  unused_ids += [str(id)]
  print("added new client "+str(id))

  return "ok"


@app.route("/status/<id>")
def check_status(id):
  if str(id) in unused_ids:
    return "not ready"
  else:
    return "ready"


@socket_.on("register", namespace="/test")
def register(message):
  global queue_of_clients, unused_ids

  print("A new client registered. Assigning oldest unused id ...")
  if len(unused_ids) == 0:
    if message["id"] is not None:
      print("Pool of unused ids is empty, using client-side id.")
      queue_of_clients += [message["id"]]
      return

    print("Err: No unused ids left and no client-side id found")
    emit("error", { "message": "could not assign id" })
    return

  client_id = unused_ids[0]
  del unused_ids[0]
  queue_of_clients += [client_id]

  emit("set_id", { "id": client_id })


@socket_.on("disconnect_request", namespace="/test")
def disconnect_request():
  @copy_current_request_context
  def can_disconnect():
    disconnect()

  session["receive_count"] = session.get("receive_count", 0) + 1
  emit("my_response", {"data": "Disconnected!", "count": session["receive_count"]}, callback=can_disconnect)


# UPDATE SPEC ######################################################################################

@socket_.on("send_spec", namespace="/test")
def send_spec(message):
  print("received new spec")
  on_update_spec(message)
  return "ok"


@socket_.on("update_spec", namespace="/test")
def update_spec(message):
  on_update_spec(message)

  update_all()


def on_update_spec(message):
  global current_spec

  if message['spec'] == None:
    return False

  current_spec = message['spec']


@app.route("/update")
def update_all():
  print("Updating all.")
  socket_.emit("broadcast_spec", { "spec": current_spec }, broadcast=True, namespace='/test')

  return "ok"


@app.route("/update/<target_id>")
def update_target(target_id):
  print("Updating all.")

  # TODO: This broadcasts the spec to every client, expecting clients to check if they are the
  # addressed target. Message should instead only be send to one particular client to avoid
  # client-side verification.
  socket_.emit("send_spec", { "spec": current_spec, "target": target_id }, broadcast=True, namespace="/test")

  return "ok"


if __name__ == "__main__":
  socket_.run(app, debug=True)
