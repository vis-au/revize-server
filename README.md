# RevizeServer
This repository contains the code for a websocket server, which can be used to distribute [Vega-lite](https://vega.github.io/vega-lite) specifications in realtime across multiple, parallel [revize](https://www.npmjs.com/package/revize)-enabled visualization clients.

Clients that wish to connect to this server need to implement the websocket interface of [revize](https://www.npmjs.com/package/revize) version 1.0.4 or higher.


## Prerequisites
RevizeServer uses ```Python 3.8.5```. We recommend setting up an (optional) [virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/) for the packages.
The project mainly builds on the [flask-socketio](https://flask-socketio.readthedocs.io/en/latest/) package to create a server for synchronizing vega-lite specifications over websockets and control the toolchain over http.

## Installation
To install all dependencies, run the following pip command on a terminal inside this directory:

```bash
pip install -r requirements.txt
```

## Getting started
With all dependencies installed, the server can be launched by running the following command inside this directory:

```
python server.py
```

This will launch a websocket server on ```localhost:5000``` for revize clients to connect to, as well as a [flask](https://flask-socketio.readthedocs.io/en/latest/) that receives HTTP requests.
The default websocket namespace for serving vega-lite specs is ```"/test"```.
The testing environment can be reached through the browser on [http://localhost:5000](localhost:5000/).


## Websocket Interface
The server provides a lightweight websocket and HTTP interface for synchronizing vega-lite specifications.
All endpoints are listed below.
HTTP endpoints have the HTTP prefix, websocket endpoints are not particularly marked.

### Configuring the Toolchain
The following endpoints allow to set up the toolchain, before any Vega-Lite specifications can be exchanged.


#### register ```{ id }```
Registers a new client in the workflow and shares the latest version and the latest Vega-lite specification with that client.

* The ```id``` property must contain a number, for example drawn from a random sample.

#### disconnect_request
Unregisters a client from the workflow.
This endpoint takes has no parameters.


#### HTTP:/add/```id```
Informs the server about a tool ```id``` that will register in the future.
By using this endpoint for multiple tools, the toolchain can be configured without having to start each tool.

* The ```id``` property must contain a number, for example drawn from a random sample.

#### HTTP:/status/```id```
Retrieves the alive-status of a particular tool, by checking whether a client using the given ```id``` has registered.
If a client has registered, the server responds with ```ready```, and if not, the server responds with ```not ready```.

* The ```id``` property must contain a number, for example drawn from a random sample.


### Exchanging Specifications
The following endpoints allow sending Vega-Lite specifications to other registered and connected tools.

#### send_spec ```{ spec }```
Sends the Vega-Lite specification ```spec``` to the server, without updating other tools.

* ```spec``` must contain a valid Vega-Lite specification (no server-side validation!).

#### update_spec ```{ spec }```
Sends the Vega-Lite specification ```spec``` to the server and triggers an update for all registered tools.

* ```spec``` must contain a valid Vega-Lite specification (no server-side validation!).

#### HTTP:/update
Distributes the Vega-Lite specification that the server received the latest to all registered clients.
This endpoint takes has no parameters.

#### HTTP:/update/```target_id```
Sends the Vega-Lite specification that the server received the latest to the tool registered under the given id.

* ```id``` must contain a number, for example drawn from a random sample.