import socket
import select

# Server configuration
SERVER_PORT = 5454
SERVER_IP = "0.0.0.0"
MANAGERS = ["Omer"]
MUTED = []


def print_client_sockets(client_sockets):
    """Prints the list of connected clients."""
    for client in client_sockets:
        print("\t", client.getpeername())


print("Setting up server...")

# Initialize server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen()

print("Listening for clients...")

# Lists to manage clients and messages
client_sockets = []
online = {}

while True:
    # Monitor sockets for activity
    readable, writable, _ = select.select([server_socket] + client_sockets, client_sockets, [])

    for current_socket in readable:
        # New client connection
        if current_socket is server_socket:
            connection, client_address = current_socket.accept()
            print(f"New client joined! {client_address}")
            client_sockets.append(connection)
            print_client_sockets(client_sockets)

        # Receiving data from a client
        else:
            try:
                name_length = int(current_socket.recv(1).decode())
                name = current_socket.recv(name_length).decode()
                if name not in online:
                    online[name] = current_socket
                if name not in MUTED:
                    timestamp = current_socket.recv(5).decode()
                    msg_length = int(current_socket.recv(3).decode())
                    message = current_socket.recv(msg_length).decode()
                    if message[:9] == "/private ":
                        message = message[9:]
                        l = message.split(":")
                        if len(l) > 1:  # Ensure valid format
                            dst = l[0].strip()
                            private_message = l[1].strip()
                            # Ensure the destination user is online
                            if dst in online:
                                neo_socket = online[dst]
                                try:
                                    # Send the private message to the recipient
                                    neo_socket.send(f"Private message from {name}: {private_message}".encode())
                                except OSError:
                                    print(f"Failed to send private message to {dst}, user might be disconnected.")
                            else:
                                # Notify the sender if the recipient is not found
                                current_socket.send(f"User {dst} is not online.".encode())
                        else:
                            current_socket.send(
                                "Invalid private message format. Use /private <username>: <message>".encode())
                        continue
                    else:
                        if message == "view-managers":
                            s = str(MANAGERS)
                            current_socket.send(s.encode())
                        if name in MANAGERS:
                            name = "@" + name
                            if "/kick " in message:
                                kicked = message[6:].strip()
                                if kicked == name:  # Prevent admin from kicking themselves
                                    current_socket.send("You cannot kick yourself!".encode())
                                elif kicked in online:
                                    ks = online[kicked]
                                    ks.send("You have been kicked from the chat by an admin!".encode())
                                    client_sockets.remove(ks)
                                    ks.close()
                                    del online[kicked]  # Remove from online users
                                else:
                                    current_socket.send(f"User {kicked} not found.".encode())
                            elif "/promote " in message:
                                neo = message[9:].strip()
                                if neo == name:  # Prevent admin from promoting themselves
                                    current_socket.send("You cannot promote yourself!".encode())
                                elif neo in MANAGERS:  # Prevent admin from promoting an admin
                                    current_socket.send("You cannot promote an admin!".encode())
                                elif neo in online:
                                    ks = online[neo]
                                    ks.send("You have been promoted to be an admin!".encode())
                                    MANAGERS.append(neo)
                                else:
                                    current_socket.send(f"User {neo} not found.".encode())
                            elif "/mute " in message:
                                muted = message[6:].strip()
                                if muted == name:  # Prevent admin from muting themselves
                                    current_socket.send("You cannot mute yourself!".encode())
                                elif muted in online:
                                    ks = online[muted]
                                    ks.send("You have been muted by an admin!".encode())
                                    MUTED.append(muted)
                                else:
                                    current_socket.send(f"User {muted} not found.".encode())

                        formatted_message = f"{timestamp} {name}: {message}"
                        print(formatted_message)
                else:
                    try:
                        timestamp = current_socket.recv(5).decode()  # Read timestamp
                        msg_length = int(current_socket.recv(3).decode())  # Read message length
                        _ = current_socket.recv(msg_length).decode()  # Read and discard message
                        current_socket.send("You are muted and cannot send messages!".encode())
                    except:
                        print(f"Error handling muted user {name}")
                    continue  # Skip further processing

                # Send the message to all clients except the sender
                for client in writable[:]:  # Iterate over a copy to avoid modification issues
                    if client.fileno() == -1:  # Check if the socket is closed
                        continue
                    if client != current_socket and "/promote" not in formatted_message:
                        try:
                            client.send(formatted_message.encode())
                        except OSError:
                            print(f"Failed to send message to {client.getpeername()}, removing it.")
                            client_sockets.remove(client)
                            client.close()
            except:
                print("\nConnection closed")
                disconnect_msg = f"{timestamp} {name} quit the chat"

                for client in writable[:]:
                    if client.fileno() == -1:
                        continue
                    if client != current_socket:
                        try:
                            client.send(disconnect_msg.encode())
                        except OSError:
                            print(f"Failed to send disconnect message to {client.getpeername()}, removing it.")
                            client_sockets.remove(client)
                            client.close()

                client_sockets.remove(current_socket)
                current_socket.close()
