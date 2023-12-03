import socket, os, time, argparse
from _thread import * 

# create a socket object
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# socket,AF_INET = address family of IPv4
# socket.SOCK_STREAM = TCP socket

serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
# SOL_SOCKET = Socket option level
# SO_REUSEADDR = Reuse socket address
# 1 = True

parser = argparse.ArgumentParser(description='Server script')
parser.add_argument('--host', type=str, help='Host IP address', default='localhost')
parser.add_argument('--port', type=int, help='Port number', default=3000)
args = parser.parse_args()

host = args.host
port = args.port

serversocket.bind((host, port))

serversocket.settimeout(0.5)

serversocket.listen(5)

clients_connected = {}

clients_registered = set()

commands = {
    '/leave': 1,        # sample: /leave
    '/register': 2,     # sample: /register <username>
    '/store': 2,        # sample: /store <filename>
    '/dir': 1,          # sample: /dir
    '/get': 2,          # sample: /get <filename>
    '/?': 1,            # sample: /?
    '/message': 30,     # sample: /message <client> <message>
    '/broadcast': 30,   # sample: /broadcast <message>
}

def client_thread(connection):
    print('Client connected')
    
    connected = True
    client_name = None
    clients_connected[connection] = client_name
    
    print(clients_connected) # for debugging purposes

    while connected: 
        try:
            command = connection.recv(1024).decode()
        except ConnectionResetError:
            print('Client disconnected')
            break # close connection if client has disconnected
        except OSError as e:
            print(f"OSError: {e}")
            break

        command_args = command.split('\n')[0].split()

        print(repr(command), command_args) # for debugging purposes

        # if command does not exist, send error message
        if not (command_args[0] in commands):
            connection.sendall('Invalid command'.encode())
            continue

        # if command exists and length of command_args != to required number of arguments, send error message
        elif command_args[0] in commands and len(command_args) != commands[command_args[0]]:
            # validation for /message and /broadcast, limit message to 30 characters
            if command_args[0] in ['/message', '/broadcast'] and len(command_args) > 30:
                connection.sendall('Error: 30 characters limit exceeded.'.encode())
                continue
            else:
                connection.sendall('Error: Command parameters mismatch.'.encode())
                continue
        
        # check if client has already registered a name
        if not (client_name in clients_registered):
            # if not, only allow /register, /leave, and /? commands
            if command_args[0] not in ['/register', '/leave', '/?']:
                connection.sendall('Error: Please register a name first.'.encode())
                continue
        else:
            # if already registered and command is /register, send error message
            if command_args[0] in ['/register']:
                connection.sendall('Error: You have already registered a name.'.encode())
                continue

        match command_args[0]:
            case '/leave':
                connection.sendall(f"Connection closed.".encode())
                broadcast_message(f"{client_name} has left the server.")

                # remove client
                clients_connected.pop(connection)
                if client_name in clients_registered:
                    clients_registered.remove(client_name)
                connection = False

            case '/register':
                client_name = command_args[1] 
                # username validation
                if client_name is None:
                    connection.sendall('Error: Please enter a valid username.'.encode())
                elif client_name in clients_registered:
                    connection.sendall('Error: Username already taken.'.encode())
                else:
                    clients_connected[connection] = client_name
                    clients_registered.add(client_name)
                    connection.sendall(f"Successfully registered as {client_name}.".encode())
                    broadcast_message(f"{client_name} has joined the server.")

            case '/dir': # list all files in server_dir
                files = os.listdir('server_dir')
                connection.sendall("Server Directory:\n".encode()+"\n".join(files).encode())

            case '/store': # from client_dir to server_dir
                file_name = command_args[1]
                file_data = ('\n'.join(command.split('\n')[1:])).encode()
                with open(f"server_dir/{file_name}", 'wb') as f:
                    f.write(file_data)
                    print(f"Successfully stored {file_name} in server_dir.")
                
                # get timestamp in format: 2023-11-06 16:48:05
                time_stamp = os.path.getmtime(f"server_dir/{file_name}")
                convert_time = time.localtime(time_stamp)
                readable_time = time.strftime("%Y-%m-%d %H:%M:%S", convert_time)

                connection.sendall(f"{client_name}<{readable_time}>: Uploaded {file_name}".encode())
                broadcast_message(f"{client_name}<{readable_time}>: Uploaded {file_name}")

            case '/get': # from server_dir to client_dir
                file_name = command_args[1]
                
                files = os.listdir('server_dir')

                if file_name not in files:
                    connection.sendall(b'0') # send 0 if file does not exist
                    connection.sendall(f"Error: {file_name} does not exist in the server.".encode())
                    continue
                
                with open(f"server_dir/{file_name}", 'rb') as f:
                    file_data = f.read()
                    connection.sendall(b'1') # send 1 if file exists
                    connection.sendall(file_data)
                    print(f"Successfully retrieved {file_name} from server_dir.")

            case '/?': # list all commands
                message = """
/? - list all commands
/join <server_ip_> <port> - join the server
/register <username> - register a username
/dir - list all files in server_dir
/store <filename> - store file from client_dir to server_dir
/get <filename> - retrieve file from server_dir to client_dir
/message <client_username> <message> (30 characters limit) - send message to specific client
/broadcast <message> (30 characters limit) - send message to all clients
/leave - leave the server
                """

                connection.sendall(message.encode())

            case '/message': # send message to specific client
                to_client = command_args[1]
                message = ' '.join(command_args[2:])

                if to_client not in clients_registered:
                    connection.sendall(f"Error: {to_client} is not registered.".encode())

                for client_conn, check_to_client in clients_connected.items():
                    if check_to_client == to_client:
                        connection.sendall(f"To {to_client}: {message}".encode())
                        client_conn.sendall(f"From {client_name}: {message}".encode())
                    else:
                        # if invalid to_client, send error message
                        connection.sendall(f"Error: {to_client} is not connected.".encode())

            case '/broadcast': # send message to all clients
                message = ' '.join(command_args[1:])
                broadcast_message(f"Broadcast from {client_name}: {message}")   

            case _: # if command does not exist, send error message
                connection.sendall('Error: Invalid command.'.encode())

        # remove client when connection is closed
        clients_connected.pop(connection)
        if client_name in clients_registered:
            clients_registered.remove(client_name)
        connection.close()
            

def broadcast_message(message):
    for client in clients_connected:
        try:
            client.sendall(message.encode())
        except Exception as e:
            print(f"Failed to send message to {client}: {e}")

while True:
    # establish connection with client
    try:
        connection, addr = serversocket.accept()
        start_new_thread(client_thread, (connection,))
    except TimeoutError:
        pass