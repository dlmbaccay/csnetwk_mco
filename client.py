# Baccay, Dominic
# Miranda, Bien
# Rana, Luis

# CSNETWK S12 - Machine Project

import socket, os, selectors, tkinter as tk
from tkinter import scrolledtext, Label, font, Entry, Button

# Create a socket object
c_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
selector = selectors.DefaultSelector()

hasJoined = False

def register_command():
  global hasJoined, c_socket # c_socket is the socket object for the client connection to the server
  # Get the command from the input field
  command = input_field.get()

  # Don't send if the command is empty
  if not len(command): return

  parameters = command.split()
  command_0 = parameters[0]

  if hasJoined == False:
    # Make sure the command is valid
    if command_0 not in ("/join", "/leave", "/register", "/store", "/dir", "/get", "/?", "/pm", "/shout"):
      register_status(system_output, "Error: Command not found.\n")
      input_field.delete(0, 'end')
      return
    
    # Check if the command is /join
    if command_0 == "/join":
      # make sure correct number of arguments
      if len(parameters) != 3:
        register_status(system_output, "Error: Command parameters mismatch.\n")
      else:
        try:
          # Connect to the server, all_words[1] is the IP address, all_words[2] is the port
          c_socket.connect((parameters[1], int(parameters[2])))
          register_status(system_output, "Successfully connected to the File Exchange Server\n")
          # system_output.insert("1.0", "Connection to the File Exchange Server is successful!\n")
          hasJoined = True
        except socket.error:
          register_status(system_output, "Error: Connection to server failed! Check if parameters are correct.\n")
    elif command_0 == "/leave":
      register_status(system_output, "Error: Server connection is not established, please connect to the server first.\n")
    elif command_0 == "/register" or command_0 == "/store" or command_0 == "/dir" or command_0 == "/get" or command_0 == "/pm" or command_0 == "/shout":
      register_status(system_output, "Error: Server connection is not established, please connect to the server first.\n")
    elif command_0 == "/?":
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
      register_status(system_output, message)

  elif hasJoined == True:
    # Make sure the command is valid
    if command_0 not in ("/join", "/leave", "/register", "/store", "/dir", "/get", "/?", "/pm", "/shout"):
      register_status(system_output, "Error: Command not found.\n")
      input_field.delete(0, 'end')
      return

    # Check if the command is /join
    if command_0 == "/join":
      # make sure correct number of arguments
      if len(parameters) != 3:
        register_status(system_output, "Error: Command parameters mismatch.\n")
      else:
        register_status(system_output, "Error: Server connection is already established.\n")
    else:
      if command_0 == "/store":
        if len(parameters) == 2: # valid number of parameters
          files = os.listdir("client_dir")
          if parameters[1] in files:
            with open(f"client_dir/{parameters[1]}", 'rb') as f:
              file_data = f.read()
              try:
                c_socket.sendall((command + "\n").encode() + file_data)
              except ConnectionResetError:
                register_status(system_output, 'Error: Server connection was interrupted.\n')

            data = c_socket.recv(1024)
            register_status(system_output, data.decode()+"\n") # Print the data received from the server
          else:
            register_status(system_output, "Error: File not found.\n")
        else:
          register_status(system_output, "Error: Command parameters mismatch.\n")
      elif command_0 == "/get":
        if len(parameters) == 2: # valid number of parameters
          try:
            c_socket.sendall(command.encode())
          except ConnectionResetError:
            register_status(system_output, 'Error: Server connection was interrupted.\n')

          header = c_socket.recv(1)

          if header == b'1':
            file_data = c_socket.recv(1024)
            with open(f"client_dir/{parameters[1]}", 'wb') as f:
              f.write(file_data)
            register_status(system_output, f"File received from Server: {parameters[1]}\n") # Print the data received from the server
          else:
            data = c_socket.recv(1024)
            print(f"{data.decode()}")
            register_status(system_output, data.decode()+"\n") # Print the data received from the server
        else:
          register_status(system_output, "Error: Command parameters mismatch.\n")
      elif command_0 == "/leave":
        if len(parameters) == 1: # valid number of parameters
          c_socket.sendall(command.encode()) # Send the command to the server

          data = c_socket.recv(1024)
          register_status(system_output, data.decode()+"\n") # Print the data received from the server
          hasJoined = False
        
          new_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a new socket object
          selector.unregister(c_socket) # Unregister the socket from the selector
          c_socket.close() # Close the socket
          c_socket = new_s # Set the socket to the new socket object
          selector.register(c_socket, selectors.EVENT_READ, handle_messages) # Register the socket to the selector
        else:
          register_status(system_output, "Error: Command parameters mismatch.\n")
      elif command_0 == "/pm":
        if len(parameters) >= 3 and len(parameters) <= 32:
          message = ' '.join(parameters[2:])
          c_socket.sendall(f"{command_0} {parameters[1]} {message}".encode())
        else:
          register_status(system_output, "Error: Command parameters mismatch.\n")
      elif command_0 == "/shout":
        if len(parameters) >= 2 and len(parameters) <= 32:
          message = ' '.join(parameters[1:])
          c_socket.sendall(f"{command_0} {message}".encode())
        else:
          register_status(system_output, "Error: Command parameters mismatch.\n")
      else: # If the command is /register, /dir, or /?
        try:
          c_socket.sendall(command.encode())
        except ConnectionResetError: # If the server was closed or the connection was interrupted
          register_status(system_output, 'Error: Connection interrupted.\n')

        data = c_socket.recv(1024) # Receive data from the socket
        register_status(system_output, data.decode()+"\n")

  input_field.delete(0, 'end') # Clear the input field

# Function to register the status of the system
def register_status(widget, text):
  widget.config (state = tk.NORMAL)
  widget.insert (tk.END, text)
  widget.config (state = tk.DISABLED)

# Function to handle messages from the server
def handle_messages():
    global c_socket
    try:
        if c_socket.fileno() == -1:
            return
        
        data = c_socket.recv(1024)
        
        if data: # If data is received
            message_output.config(state=tk.NORMAL)
            message_output.insert(tk.END, data.decode() + "\n")
            message_output.config(state=tk.DISABLED)
    except ConnectionResetError:
        pass

# Function to check for messages from the server
def check_messages():
    events = selector.select(timeout=0)
    for key, _ in events: # For each socket that has a message ready to be read
        callback = key.data
        callback()
    root.after(1000, check_messages)

# Create the main window
root = tk.Tk()

# Start checking for messages
root.after(1000, check_messages)

# Set the font
verdana = font.Font(family='Verdana', size=10)

# input field/label

input_field_label= Label(root, text="Register a command", fg='black', font=verdana)
input_field_label.grid(row=0, column=0, columnspan=2)

input_field = Entry(root)
input_field.grid(row=1, column=0, columnspan=2)

# send button
send_button = Button(root, text="Send", command=register_command)
send_button.grid(row=2, column=0, columnspan=2)
root.bind('<Return>', lambda event=None: send_button.invoke()) # Bind the enter key to the send button

# commands label
commands_label = Label(root, text="/? : show command list", fg='black', font=verdana)
commands_label.grid(row=3, column=0, columnspan=2)

# system output/label
system_output_label = Label(root, text="System:", fg='black', font=verdana)
system_output_label.grid(row=4, column=0)

system_output = scrolledtext.ScrolledText(root, fg='black', font=verdana, state="disabled", width=50, height=30)
system_output.grid(row=5, column=0)

# message output/label
message_output_label = Label(root, text="Messages:", fg='black', font=verdana)
message_output_label.grid(row=4, column=1)

message_output = scrolledtext.ScrolledText(root, fg='black', font=verdana, state="disabled", width=50, height=30)
message_output.grid(row=5, column=1)

# Set the window title, size, and position
root.title('File Exchange System - Client')
root.geometry("850x600")
root.resizable(False, False)
root.eval('tk::PlaceWindow . center')

# Register the socket to the selector
selector.register(c_socket, selectors.EVENT_READ, handle_messages) 

# Start the GUI
root.mainloop()