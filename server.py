# Baccay, Dominic
# Miranda, Bien
# Rana, Luis

# CSNETWK S12 - Machine Project

import socket, time, os, argparse
from _thread import *

# Create a socket object
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Set the SO_REUSEADDR option on the socket
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, default='127.0.0.1')
parser.add_argument('--port', type=int, default=12345)
args = parser.parse_args()

# python server.py --host 127.0.0.1 --port 12345
# /join 127.0.0.1 12345

# Bind to the port
serversocket.bind((args.host, args.port))

# Set socket listening timeout
serversocket.settimeout(0.2)

# Listen for incoming connections
serversocket.listen(5)

# Dictionary to store connections and client names
clients_connected = {}

# Set to store client names
clients_registered = set()

# Hashmap to keep track of commands and required number of args
commands = {
    '/leave':1,     # sample: /leave
    '/register':2,  # sample: /register <handle>
    '/store':2,     # sample: /store <filename>
    '/dir':1,       # sample: /dir
    '/get':2,       # sample: /get <filename>
    '/?':1,         # sample: /?
    '/pm':32,       # sample: /pm <handle> <message_string(up to 30 words)>
    '/shout':32     # sample: /shout <message_string(up to 30 words)>
}

def client_thread(connection):
    # Initialize connected as True
    connected = True
    client_name = ''
    clients_connected[connection] = client_name

    print(clients_connected)

    while connected:
        try:
            # Receive the command input
            command = connection.recv(1024).decode()
        except ConnectionResetError:
            # Connection forcibly closed by remote host
            break

        command_args = command.split('\n')[0].split()

        print(repr(command), command_args)

        # If the command is a command and the length of the command_args is not equal to the required number of parameters for the command then send an error message
        if command_args[0] in commands and len(command_args) != commands[command_args[0]]:
            if (command_args[0] == '/pm' or command_args[0] == '/shout') and len(command_args) <= 32:
              pass
            elif (command_args[0] == '/pm' or command_args[0] == '/shout') and not (len(command_args) <= 32):
              connection.sendall(f"Error: There is a limit of 30 words.".encode())
              continue
            else:
              connection.sendall(f"Error: Command parameters mismatch.".encode())
              continue
        elif not (command_args[0] in commands):
            connection.sendall(f"Error: Command not found.".encode())
            continue

        # Check if the client has registered a name
        if not (client_name in clients_registered):
            # If the client has not registered a name, only allow /register and /? commands
            if command_args[0] not in ['/register', '/?', '/leave']:
                # Quick workaround for the error message display issue for /get until redesigned
                if command_args[0] == '/get':
                    connection.sendall(b'0')
                connection.sendall(f"Error: You must register a username before executing other commands.".encode())
                continue
        else:
            if command_args[0] == '/register':
                connection.sendall(f"Error: You have already registered a username.".encode())
                continue

        match command_args[0]:
            case "/register":
                client_name = command_args[1]
                if (client_name in clients_registered) or client_name is None: # Check if the client name is already in use or invalid
                    print(f"Debugging: Client name {client_name} is already in use or invalid.") # debugging
                    connection.sendall(f"Error: Registration failed. Handle or alias already exists.".encode()) # Send error message to the client upon failed registration
                else:
                    print(f"Debugging: Client registered as {client_name}") # debugging
                    connection.sendall(f"Welcome {client_name}!".encode()) # Send success message to the client upon successful registration
                    clients_connected[connection] = client_name # Add the client to the dictionary of connected clients
                    clients_registered.add(client_name) # Add the client name to the set of registered clients
            case "/leave":
                # Send success message to the client upon disconnection
                connection.sendall(f"Connection closed.".encode())

                # Remove the client from the dictionary of connected clients
                clients_connected.pop(connection)
                if client_name in clients_registered:
                    clients_registered.remove(client_name)
                connected = False
            case "/dir":
                # Get the list of all files in the directory
                files = os.listdir("server_dir")
                # Send the list of files to the client separated by a newline with a label that says Server Directory:
                connection.sendall("Server Directory:\n".encode()+"\n".join(files).encode())
            case "/store":
                file_name = command_args[1]
                # Receive the file from the client
                file_data = ('\n'.join(command.split('\n')[1:])).encode()
                # Open the file in binary mode
                with open(f"server_dir/{file_name}", 'wb') as f:
                    f.write(file_data)
                    print(f"Debugging: File {file_name} received and saved.") # debugging

                # Get timestamp of the file (last modified)
                timestamp = os.path.getmtime(f"server_dir/{file_name}")
                format_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

                # Send success message to the client upon storing
                connection.sendall(f"{client_name}<{format_time}>: Uploaded {file_name}".encode())     
            case "/get":
                file_name = command_args[1]
                # Get the list of all files in the directory
                files = os.listdir("server_dir")
                # Check if the file exists in the directory
                if file_name in files:
                    # Open the file in binary mode
                    with open(f"server_dir/{file_name}", 'rb') as f:
                        # Read the file
                        file_data = f.read()
                        # Send the header first
                        connection.sendall(b'1') # '1' indicates that file data will follow
                        # Send the file to the client
                        connection.sendall(file_data)
                else:
                    # Send the header first
                    connection.sendall(b'0') # '0' indicates that an error message will follow
                    # Send error message to the client upon file not found
                    connection.sendall(f"Error: File not found in the server.".encode())
            case "/pm":
                # Send the message to another client
                recipient = command_args[1]
                message = ' '.join(command_args[2:])

                # Check if the recipient is registered in the server
                if recipient in clients_registered:
                    # Send the message to the recipient
                    for client_connection, recipient_name in clients_connected.items():
                        if recipient_name == recipient:
                            connection.sendall(f"To {recipient}: {message}".encode())
                            client_connection.sendall(f"From {client_name}: {message}".encode())
                else:
                    # Send error message to the client upon an invalid recipient
                    connection.sendall(f"Error: Recipient not found.".encode())
            case "/shout":
                message = ' '.join(command_args[1:])
                # Send the broadcast message to all clients
                shout_message(f"Shouted by {client_name}: {message}")
            case "/?":
                message = """
Commands:
/?
/join <server_IP> <port>
/leave
/register <username>
/store <filename>
/dir
/get <filename>
/pm <username> <message>
/shout <message>\n
"""
                connection.sendall(message.encode()) 
            case _: # if none of the above commands are matched
                # Send an error message to the client upon an invalid command
                connection.sendall(f"Error: Command not found.".encode())

    # Remove the client from connected clients
    clients_connected.pop(connection)
    if client_name in clients_registered:
        clients_registered.remove(client_name)
    connection.close()

def shout_message(message):
    for client_connection, client_name in clients_connected.items():
        try:
            client_connection.sendall(message.encode())
        except Exception as e:
            print(f"Failed to send message to {client_connection}: {e}")

while True:
    # Establish a connection with the client
    try:
        clientsocket, addr = serversocket.accept()
        start_new_thread(client_thread, (clientsocket, ))
    except TimeoutError:
        pass
