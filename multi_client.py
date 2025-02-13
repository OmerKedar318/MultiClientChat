import socket
import select
import msvcrt
from datetime import datetime

my_socket = socket.socket()
connected = False

while not connected:
    try:
        my_socket.connect(('127.0.0.1', 5454))
        connected = True
    except:
        print("Is the server online?")

while True:
    username = input("Enter username (max 9 characters): ")
    if len(username) < 10 and username[0] != "@":
        break

print("Start typing a new message...")

message = ""

while True:
    # Check for incoming messages
    readable, _, _ = select.select([my_socket], [], [], 0.1)

    # Check for user input
    if msvcrt.kbhit():
        key = msvcrt.getch()

        # If Enter is pressed, send the message
        if key == b'\r':
            current_time = datetime.now().strftime("%H:%M")

            if message == "quit":  # Exit condition
                message = f"{len(username)}{username}{current_time}"
                my_socket.send(message.encode())
                print("Connection closed")
                break

            print(f"\rMessage sent: {message}", flush=True)
            formatted_message = f"{len(username)}{username}{current_time}{len(message):03}{message}"
            my_socket.send(formatted_message.encode())

            message = ""

        # Handle Backspace key
        elif key == b'\x08' and message:
            message = message[:-1]
            print(f"\r{message} ", end='', flush=True)

        # Add character to message
        else:
            message += key.decode()
            print(f"\r{message} ", end='', flush=True)

    # Process incoming messages
    for msg in readable:
        received_msg = msg.recv(1024).decode()
        if "/mute" not in received_msg and "view-managers" not in received_msg:
            print(f"\n{received_msg}")
        if "You have been kicked from the chat by an admin!" in received_msg:
            exit()
