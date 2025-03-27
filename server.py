import socket
import threading
import sqlite3
import sys

# Database setup
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT UNIQUE
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS group_members (
        group_id INTEGER,
        username TEXT,
        FOREIGN KEY(group_id) REFERENCES groups(id),
        FOREIGN KEY(username) REFERENCES users(username)
    )
    """)
    conn.commit()
    conn.close()

init_db()

# Server setup
HOST = "0.0.0.0"  # Can be replaced with the actual IP or host
PORT = 12345
clients = {}  # This will store active client connections
server_socket = None

def handle_client(client, addr):
    username = None
    try:
        while True:
            msg = client.recv(1024).decode("utf-8")
            if not msg:
                break

            if msg.startswith("REGISTER:"):
                _, user, pwd = msg.split(":")
                if register_user(user, pwd):
                    client.send("REGISTER_SUCCESS".encode("utf-8"))
                else:
                    client.send("REGISTER_FAIL".encode("utf-8"))
            elif msg.startswith("LOGIN:"):
                _, user, pwd = msg.split(":")
                if check_login(user, pwd):
                    username = user
                    clients[username] = client  # Add the client to the active user list
                    client.send("LOGIN_SUCCESS".encode("utf-8"))
                else:
                    client.send("LOGIN_FAIL".encode("utf-8"))
            elif msg.startswith("MSG:") and username:
                _, target, content = msg.split(":", 2)
                if target == "Global":
                    broadcast(f"{username}: {content}")
                else:
                    send_dm(username, target, content)
            elif msg.startswith("CREATE_GROUP:") and username:
                _, group_name = msg.split(":", 1)
                create_group(group_name, username)
                client.send(f"GROUP_CREATED:{group_name}".encode("utf-8"))
            elif msg.startswith("JOIN_GROUP:") and username:
                _, group_name = msg.split(":", 1)
                join_group(group_name, username)
                client.send(f"JOINED_GROUP:{group_name}".encode("utf-8"))
            elif msg.startswith("USERLIST:"):
                users = get_user_list()  # Get list of usernames from clients dictionary
                client.send(f"USERLIST:{','.join(users)}".encode("utf-8"))
            elif msg.startswith("STOP_SERVER:"):
                shutdown_server(client)
                break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if username in clients:
            del clients[username]  # Remove the user from the active list on disconnect
        client.close()

def register_user(username, password):
    try:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def check_login(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

def broadcast(message):
    for client in clients.values():
        try:
            client.send(message.encode("utf-8"))
        except:
            pass

def send_dm(from_user, to_user, message):
    if to_user in clients:
        clients[to_user].send(f"DM from {from_user}: {message}".encode("utf-8"))

def create_group(group_name, creator):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO groups (group_name) VALUES (?)", (group_name,))
    group_id = c.lastrowid
    c.execute("INSERT INTO group_members (group_id, username) VALUES (?, ?)", (group_id, creator))
    conn.commit()
    conn.close()

def join_group(group_name, username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id FROM groups WHERE group_name = ?", (group_name,))
    group = c.fetchone()
    if group:
        group_id = group[0]
        c.execute("INSERT INTO group_members (group_id, username) VALUES (?, ?)", (group_id, username))
        conn.commit()
    conn.close()

def get_user_list():
    # Return a list of all users currently connected, from the `clients` dictionary
    return list(clients.keys())

def shutdown_server(client):
    """Shutdown the server and close all connections."""
    client.send("Server is shutting down...".encode("utf-8"))
    print("Server is shutting down...")
    for c in clients.values():
        try:
            c.send("Server is shutting down. Disconnecting...".encode("utf-8"))
            c.close()
        except:
            pass
    if server_socket:
        server_socket.close()
    sys.exit(0)

# Server listening
def start_server():
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server running on {HOST}:{PORT}...")
    
    # Server CLI for graceful shutdown
    threading.Thread(target=server_cli, daemon=True).start()

    while True:
        client, addr = server_socket.accept()
        print(f"Connection from {addr}")
        threading.Thread(target=handle_client, args=(client, addr), daemon=True).start()

def server_cli():
    """Handle server CLI input to gracefully shut down the server."""
    while True:
        cmd = input("Server CLI (type 'shutdown' to stop server): ").strip()
        if cmd.lower() == 'shutdown':
            print("Shutting down server...")
            shutdown_server(None)
            break

if __name__ == "__main__":
    start_server()
