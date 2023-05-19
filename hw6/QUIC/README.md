# QUIC
## QUICServer
### Methods
* `def listen(self, sockaddr)`
  * Create a UDP socket. The UDP socket is bound to the sockaddr.
* `def accept(self)`
  * Waiting for a client to establish the connection.
  * The QUICServer can only maintain a connection with one client.
* `def send(self, stream_id, data, end=False)`
  * Send data to the stream identified by stream_id.
  * If end=True, the data represents the end of the stream.
* `def recv(self)`
  * `return stream_id, recv_bytes, flags`
  * If flags=1, it means that the end of the stream has been reached.
* `def close(self)`
  * Close the QUICServer
## QUICClient
### Methods
* `def connect(self, sockaddr)`
  * Create a UDP socket and connect to the QUICServer.
* `def send(self, stream_id, data, end=False)`
  * Send data to the stream identified by stream_id.
  * If end=True, the data represents the end of the stream.
* `def recv(self)`
  * `return stream_id, recv_bytes, flags`
  * If flags=1, it means that the end of the stream has been reached.
* `def drop(self, stream_id)`
  * Drop the data on the stream identified by stream_id.
* `def close(self)`
  * Close the QUICServer
