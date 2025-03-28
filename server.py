import socket
import threading

class ChatServer:
    def __init__(self):
        self.users = {}  # Store users in a dictionary (username: password)
        self.clients = {}  # Store client connections (username: client_socket)
        self.groups = {"Global": []}  # Example: Default group for global chat
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', 12345))
        self.server_socket.listen(5)
        print("Server started on port 12345...")

    def handle_client(self, client_socket, client_address):
        try:
            client_socket.send(b"Welcome to the server!\n")
            while True:
                message = client_socket.recv(1024).decode("utf-8")
                if not message:
                    break

                print(f"Received message: {message}")

                if message.startswith("LOGIN:"):
                    self.handle_login(client_socket, message)
                
                elif message.startswith("REGISTER:"):
                    self.handle_register(client_socket, message)

                elif message.startswith("MSG:"):
                    self.handle_message(client_socket, message)

                elif message.startswith("CREATE_GROUP:"):
                    self.handle_create_group(client_socket, message)

        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def handle_login(self, client_socket, message):
        _, username, password = message.split(":")
        
        if username in self.users and self.users[username] == password:
            self.clients[username] = client_socket  # Save the client connection
            client_socket.send("LOGIN_SUCCESS".encode("utf-8"))
        else:
            client_socket.send("LOGIN_FAIL".encode("utf-8"))

    def handle_register(self, client_socket, message):
        _, username, password = message.split(":")
        
        if username not in self.users:
            self.users[username] = password  # Register new user
            client_socket.send("REGISTER_SUCCESS".encode("utf-8"))
            print(f"User {username} registered successfully.")
        else:
            client_socket.send("REGISTER_FAIL".encode("utf-8"))
            print(f"Registration failed for {username}: Username already exists.")

    def handle_message(self, client_socket, message):
        _, target_group, sender, msg = message.split(":", 3)

        if target_group == "Global":
            self.broadcast_message(f"{sender}: {msg}", "Global")
        elif target_group in self.groups:
            self.broadcast_message(f"{sender}: {msg}", target_group)
        else:
            client_socket.send("GROUP_NOT_FOUND".encode("utf-8"))

    def broadcast_message(self, message, group_name):
        if group_name == "Global":
            # Send to all connected clients in the "Global" chat
            for username, client_socket in self.clients.items():
                try:
                    client_socket.send(message.encode("utf-8"))
                except Exception as e:
                    print(f"Error sending message to {username}: {e}")

    def handle_create_group(self, client_socket, message):
        _, group_name = message.split(":")
        
        if group_name not in self.groups:
            self.groups[group_name] = []  # Create new group
            client_socket.send(f"GROUP_CREATED:{group_name}".encode("utf-8"))
            print(f"Group {group_name} created successfully.")
        else:
            client_socket.send("GROUP_EXISTS".encode("utf-8"))
            print(f"Group {group_name} already exists.")

    def start(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"New connection: {client_address}")
            threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()

if __name__ == "__main__":
    server = ChatServer()
    server.start()
