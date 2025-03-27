import socket
import threading
import sqlite3
import traceback

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
    conn.commit()
    conn.close()

init_db()

# Server setup
HOST = "0.0.0.0"
PORT = 12345
clients = {}
groups = {"Global": []}  # Initialize Global group by default
active_users = set()

# Thread Lock for safe shared access
clients_lock = threading.Lock()

def handle_client(client, addr):
    username = None
    try:
        while True:
            msg = client.recv(1024).decode("utf-8")
            if not msg:  # Client disconnected
                break
            
            print(f"Received message: {msg}")  # Debugging print
            
            if msg.startswith("REGISTER:"):
                _, user, pwd = msg.split(":")
                if register_user(user, pwd):
                    client.send("REGISTER_SUCCESS".encode("utf-8"))
                else:
                    client.send("REGISTER_FAIL".encode("utf-8"))
            
            elif msg.startswith("LOGIN:"):
                _, user, pwd = msg.split(":")
                login_result = check_login(user, pwd)
                
                if login_result:
                    with clients_lock:
                        if user in active_users:
                            client.send("ALREADY_LOGGED_IN".encode("utf-8"))
                        else:
                            username = user
                            clients[username] = client
                            active_users.add(username)
                            # Add user to Global group by default
                            if "Global" not in groups:
                                groups["Global"] = []
                            if username not in groups["Global"]:
                                groups["Global"].append(username)
                            
                            client.send("LOGIN_SUCCESS".encode("utf-8"))
                            broadcast(f"Server: {username} has joined the chat")
                            send_groups_to_client(client)
                else:
                    client.send("LOGIN_FAIL".encode("utf-8"))
            
            elif msg.startswith("MSG:") and username:
                try:
                    _, recipient_type, recipient, content = msg.split(":", 3)
                    if recipient_type == "Global":
                        broadcast(f"{username}: {content}")
                    elif recipient_type == "DM":
                        send_dm(recipient, f"{username} (DM): {content}")
                    elif recipient_type == "GROUP":
                        if recipient in groups:
                            send_group_message(recipient, f"{username} ({recipient}): {content}")
                except Exception as e:
                    print(f"Error processing message: {e}")
                    traceback.print_exc()
            
            elif msg.startswith("CREATE_GROUP:") and username:
                _, group_name = msg.split(":")
                if create_group(group_name, username):
                    client.send(f"GROUP_CREATED:{group_name}".encode("utf-8"))
                    send_groups_to_all_clients()
                else:
                    client.send(f"GROUP_CREATE_FAIL:{group_name}".encode("utf-8"))
    
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
        traceback.print_exc()
    
    finally:
        # Always clean up after the client
        if username:
            with clients_lock:
                if username in clients:
                    del clients[username]
                if username in active_users:
                    active_users.remove(username)
                broadcast(f"Server: {username} has left the chat")
        
        try:
            client.close()
        except:
            pass

def send_groups_to_client(client):
    group_list = ":".join(groups.keys())
    try:
        client.send(f"UPDATE_GROUPS:{group_list}".encode("utf-8"))
    except:
        pass

def send_groups_to_all_clients():
    group_list = ":".join(groups.keys())
    broadcast(f"UPDATE_GROUPS:{group_list}")

def broadcast(message):
    with clients_lock:
        for client in clients.values():
            try:
                client.send(message.encode("utf-8"))
            except Exception as e:
                print(f"Error broadcasting message: {e}")

def send_dm(username, message):
    with clients_lock:
        if username in clients:
            client = clients[username]
            try:
                client.send(message.encode("utf-8"))
            except Exception as e:
                print(f"Error sending DM to {username}: {e}")

def send_group_message(group_name, message):
    if group_name in groups:
        for user in groups[group_name]:
            send_dm(user, message)

def create_group(group_name, creator):
    with clients_lock:
        # Prevent duplicate group names and invalid names
        if group_name in groups or not group_name or group_name == "Select Group":
            return False
        
        groups[group_name] = [creator]
        return True

def register_user(username, password):
    # Basic input validation
    if not username or not password:
        return False
    
    try:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # User already exists
        return False

def check_login(username, password):
    # Basic input validation
    if not username or not password:
        return False
    
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    result = c.fetchone()
    conn.close()
    return result is not None

# Server loop
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server started on {HOST}:{PORT}")

    try:
        while True:
            client, addr = server_socket.accept()
            print(f"New connection from {addr}")
            threading.Thread(target=handle_client, args=(client, addr), daemon=True).start()
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()