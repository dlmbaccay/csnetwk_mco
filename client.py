import socket, os, selectors, tkinter as tk
from tkinter import scrolledtext

# create a socket object
clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
selector = selectors.DefaultSelector()

hasJoined = False

def register_command():
    global hasJoined, clientsocket

    command = input_field.get()

    if not len(command):
        return # do nothing if command is empty
    
    parameters = command.split()
    prefix_command = parameters[0]

    if hasJoined == False:
        # allow /join, /leave, /? initially
        if (prefix_command not in ['/join', '/leave', '/?']):
            # print("Error: Please join the server first.")
            register_status(system_output, "Error: Please join the server first.")
            input_field.delete(0, tk.END)
            return
        
        if prefix_command == '/join':
            if len(parameters) != 3:
                # print("Error: Command parameters mismatch.")
                register_status(system_output, "Error: Command parameters mismatch.")
                return

            try:
                # connect to server
                clientsocket.connect((parameters[1], int(parameters[2])))
                # selector.register(clientsocket, selectors.EVENT_READ) # for reading data from server
                # print("Successfully joined the server.")
                register_status(system_output, "Successfully joined the server.")
                hasJoined = True
            except socket.error:
                # print("Error: ", e)
                register_status(system_output, f"Error: Connection interrupted.")
                return
            
        if prefix_command == '/leave':
            # print("Error: You have not joined the server yet.")
            register_status(system_output, "Error: You have not joined the server yet.")
            return
        
        if prefix_command == '/?':
            message = """
/? 
-- list all commands
/join <server_ip> <port>
-- join the server
/leave 
-- leave the server
            """

            # print(message)
            register_status(system_output, message)
            return
        
        input_field.delete(0, tk.END)
    
    elif hasJoined == True:
        # allowed commands: /join, /register, /leave, /?, /dir, /store, /get, /message, /broadcast
        if prefix_command not in ['/join', '/register', '/leave', '/?', '/dir', '/store', '/get', '/message', '/broadcast']:
            # print("Error: Invalid command.")
            register_status(system_output, "Error: Invalid command.")
            return
        
        if prefix_command == '/register':
            if len(parameters) != 2:
                # print("Error: Command parameters mismatch.")
                register_status(system_output, "Error: Command parameters mismatch.")
                return
            
            try:
                clientsocket.sendall(command.encode())
            except ConnectionResetError:
                # print("Error: Connection interrupted.")
                register_status(system_output, "Error: Connection interrupted.")
                return
            
            data = clientsocket.recv(1024)
            print(data.decode())

        if prefix_command == '/join':
            if len(parameters) != 3:
                # print("Error: Command parameters mismatch.")
                register_status(system_output, "Error: Command parameters mismatch.")
                return
            else:
                # print("Error: You have already joined the server.")
                register_status(system_output, "Error: You have already joined the server.")
                return
        
        if prefix_command == '/store':
            if len(parameters) != 2:
                # print("Error: Command parameters mismatch.")
                register_status(system_output, "Error: Command parameters mismatch.")
                return
            
            files = os.listdir('client_dir')
            if parameters[1] not in files:
                # print("Error: File does not exist.")
                register_status(system_output, "Error: File does not exist.")
                return
            
            # send file to server
            with open(f'client_dir/{parameters[1]}', 'rb') as f:
                file_data = f.read()
                try:
                    clientsocket.sendall((command + "/n").encode() + file_data)
                except ConnectionResetError:
                    # print("Error: Connection interrupted.")
                    register_status(system_output, "Error: Connection interrupted.")
                    return
                
                data = clientsocket.recv(1024)
                if data == b'1':
                    # print(f"Successfully stored {parameters[1]} to server_dir.")
                    register_status(system_output, f"Successfully stored {parameters[1]} to server_dir.")
                else:
                    # print("Error: Failed to store file to server_dir.")
                    register_status(system_output, "Error: Failed to store file to server_dir.")
                    return
        
        if prefix_command == '/get':
            if len(parameters) != 2:
                # print("Error: Command parameters mismatch.")
                register_status(system_output, "Error: Command parameters mismatch.")
                return
            
            try:
                clientsocket.sendall(command.encode())
            except ConnectionResetError:
                # print("Error: Connection interrupted.")
                register_status(system_output, "Error: Connection interrupted.")
                return
            
            header = clientsocket.recv(1024)

            if header == b'0':
                print("Error: File does not exist.")
                return
            elif header == b'1':
                file_data = clientsocket.recv(1024)
                with open(f'client_dir/{parameters[1]}', 'wb') as f:
                    f.write(file_data)
                    # print(f"Successfully retrieved {parameters[1]} from server_dir.")
                    register_status(system_output, f"Successfully retrieved {parameters[1]} from server_dir.")
            else:
                # print("Error: Failed to retrieve file from server_dir.")
                register_status(system_output, "Error: Failed to retrieve file from server_dir.")
                return
            
        if prefix_command == '/leave':
            if len(parameters) != 1:
                print("Error: Command parameters mismatch.")
                return
            
            clientsocket.sendall(command.encode())

            data = clientsocket.recv(1024)
            if data == b'1':
                # print("Successfully left the server.")
                register_status(system_output, "Successfully left the server.")
                hasJoined = False
            else:
                # print("Error: Failed to leave the server.")
                register_status(system_output, "Error: Failed to leave the server.")
                return
            
            # create a new socket object
            new_clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # unregister old socket object and register new socket
            selector.unregister(clientsocket)
            clientsocket.close()
            clientsocket = new_clientsocket
            selector.register(clientsocket, selectors.EVENT_READ)

        if prefix_command == '/?':
            message = """
/?
-- list all commands
/join <server_ip> <port>
-- join the server
/register <username>
-- register a username
/leave
-- leave the server
/dir
-- list all files in server_dir
/store <filename>
-- store file from client_dir to server_dir
/get <filename>
-- retrieve file from server_dir to client_dir
/message <client_username> <message> (30 characters limit)
-- send message to specific client
/broadcast <message> (30 characters limit)
-- send message to all clients
            """

            # print(message)
            register_status(system_output, message)
            return

        input_field.delete(0, tk.END)
    else:
        try:
            clientsocket.sendall(command.encode())
        except ConnectionResetError:
            # print("Error: Connection interrupted.")
            register_status(system_output, "Error: Connection interrupted.")
            return
        
        data = clientsocket.recv(1024)
        print(data.decode())

    input_field.delete(0, tk.END)
    
def register_status(widget, status):
    widget.config (state = tk.NORMAL)
    widget.insert (tk.END, status)
    widget.config (state = tk.DISABLED)

def handle_messages():
    global clientsocket

    try:
        if clientsocket.fileno() == -1:
            return # closed socket, do nothing
        data = clientsocket.recv(1024)
        if data:
            uni_broadcast_output.config(state=tk.NORMAL)
            uni_broadcast_output.insert(tk.END, "> " + data.decode() + "\n")
            uni_broadcast_output.config(state=tk.DISABLED)
    except ConnectionResetError:
        # print("Error: Connection interrupted.")
        register_status(system_output, "Error: Connection interrupted.")
        return

def check_messages():
    events = selector.select(timeout=0)
    for key, _ in events:
        callback = key.data
        callback()
    root.after (1000, check_messages)


root = tk.Tk()

root.after(1000, check_messages)

label = tk.Label(root, text="Enter a command", fg="black", font=("Helvetica", 16))
label.grid(row=0, column=0, columnspan=2)

input_field = tk.Entry(root)
input_field.grid(row=3, column=0, columnspan=2)

send_button = tk.Button(root, text="Send", command=register_command)
send_button.grid(row=4, column=0, columnspan=2)

# system_output and unicast/broadcast_output

system_output_label = tk.Label(root, text="System Output", fg="black", font=("Helvetica", 16))
system_output_label.grid(row=5, column=0)

system_output = scrolledtext.ScrolledText(root, width=40, height=25, state=tk.DISABLED)
system_output.grid(row=6, column=0)

uni_broadcast_output_label = tk.Label(root, text="Broadcast/Unicast Output", fg="black", font=("Helvetica", 16))
uni_broadcast_output_label.grid(row=5, column=1)

uni_broadcast_output = scrolledtext.ScrolledText(root, width=40, height=25, state=tk.DISABLED)
uni_broadcast_output.grid(row=6, column=1)

root.title("CSNETWK Machine Project - Client")
root.geometry("630x475")

selector.register(clientsocket, selectors.EVENT_READ, handle_messages)

root.mainloop()