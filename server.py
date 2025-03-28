import socket
import threading

HOST = "0.0.0.0"
PORT = 12345

clients = {}  # username -> client_socket
users = {}  # username -> password
groups = {"Global": set()}  # group_name -> set of usernames

lock = threading.Lock()

def broadcast(message, group="Global", sender=""):
    """Send a message to all users in a group."""
    if group in groups:
        for user in groups[group]:
            if user in clients:
                try:
                    clients[user].send(f"{sender}: {message}".encode("utf-8"))
                except:
                    del clients[user]

def handle_client(client_socket):
    """Handles client connection."""
    username = None
    try:
        while True:
            data = client_socket.recv(1024).decode("utf-8")
            if not data:
                break

            parts = data.split(":")
            command = parts[0]

            if command == "LOGIN":
                username, password = parts[1], parts[2]
                if username in users and users[username] == password:
                    with lock:
                        clients[username] = client_socket
                        groups["Global"].add(username)
                    client_socket.send("LOGIN_SUCCESS".encode("utf-8"))
                else:
                    client_socket.send("LOGIN_FAIL".encode("utf-8"))

            elif command == "REGISTER":
                username, password = parts[1], parts[2]
                if username in users:
                    client_socket.send("REGISTER_FAIL".encode("utf-8"))
                else:
                    users[username] = password
                    client_socket.send("REGISTER_SUCCESS".encode("utf-8"))

            elif command == "MSG":
                msg_type, recipient, message = parts[1], parts[2], ":".join(parts[3:])
                if msg_type == "DM":
                    if recipient in clients:
                        clients[recipient].send(f"[DM] {username}: {message}".encode("utf-8"))
                elif msg_type == "GROUP":
                    broadcast(message, group=recipient, sender=username)
                else:
                    broadcast(message, sender=username)

            elif command == "CREATE_GROUP":
                group_name = parts[1]
                if group_name not in groups:
                    groups[group_name] = set()
                    client_socket.send(f"GROUP_CREATED:{group_name}".encode("utf-8"))
                else:
                    client_socket.send("GROUP_EXISTS".encode("utf-8"))

    except:
        pass

    finally:
        if username:
            with lock:
                if username in clients:
                    del clients[username]
                for group in groups.values():
                    if username in group:
                        group.remove(username)
        client_socket.close()

def start_server():
    """Starts the server."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server started on {HOST}:{PORT}")

    while True:
        client_socket, _ = server.accept()
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()

if __name__ == "__main__":
    start_server()
