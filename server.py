import socket
import threading
import sqlite3

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

def handle_client(client, addr):
    username = None
    try:
        while True:
            msg = client.recv(1024).decode("utf-8")
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
                    clients[username] = client
                    client.send("LOGIN_SUCCESS".encode("utf-8"))
                else:
                    client.send("LOGIN_FAIL".encode("utf-8"))
            elif msg.startswith("MSG:") and username:
                _, content = msg.split(":", 1)
                broadcast(f"{username}: {content}")
    except:
        pass
    finally:
        if username in clients:
            del clients[username]
        client.close()

def register_user(username, password):
    try:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def check_login(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

def broadcast(message):
    for client in clients.values():
        try:
            client.send(message.encode("utf-8"))
        except:
            pass

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server listening on {HOST}:{PORT}")
    
    while True:
        client, addr = server.accept()
        print(f"New connection from {addr}")
        threading.Thread(target=handle_client, args=(client, addr)).start()

if __name__ == "__main__":
    start_server()
