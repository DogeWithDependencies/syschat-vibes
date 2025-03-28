import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Client")
        
        self.username = None
        self.HOST = None
        self.PORT = 12345
        self.client_socket = None
        
        self.setup_connection()

    def setup_connection(self):
        connection_window = tk.Toplevel(self.root)
        connection_window.title("Connect to Server")
        
        tk.Label(connection_window, text="Server IP:").pack()
        ip_entry = tk.Entry(connection_window)
        ip_entry.pack()
        
        def connect():
            self.HOST = ip_entry.get()
            if not self.HOST:
                messagebox.showerror("Error", "Server IP is required!")
                return
            
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.HOST, self.PORT))
                connection_window.destroy()
                self.create_login_screen()
            except Exception as e:
                messagebox.showerror("Connection Failed", f"Could not connect to server: {e}")
        
        tk.Button(connection_window, text="Connect", command=connect).pack()
        connection_window.protocol("WM_DELETE_WINDOW", self.root.quit)

    def create_login_screen(self):
        self.clear_window()
        
        tk.Label(self.root, text="Username:").pack()
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack()
        
        tk.Label(self.root, text="Password:").pack()
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack()
        
        tk.Button(self.root, text="Login", command=self.login).pack()
        tk.Button(self.root, text="Register", command=self.register).pack()

    def create_chat_screen(self):
        self.clear_window()

        self.chat_area = scrolledtext.ScrolledText(self.root, state='disabled', height=20)
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        message_frame = tk.Frame(self.root)
        message_frame.pack(fill=tk.X)

        self.msg_entry = tk.Entry(message_frame)
        self.msg_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.msg_entry.bind('<Return>', lambda event: self.send_message())

        tk.Button(message_frame, text="Send", command=self.send_message).pack(side=tk.RIGHT)

        threading.Thread(target=self.receive_messages, daemon=True).start()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def send_message(self):
        message = self.msg_entry.get().strip()
        if not message:
            return
        
        try:
            self.client_socket.send(f"MSG:Global:Global:{message}".encode("utf-8"))
            self.msg_entry.delete(0, tk.END)
        except:
            messagebox.showerror("Error", "Failed to send message!")

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode("utf-8")
                if not message:
                    break
                self.chat_area.config(state='normal')
                self.chat_area.insert(tk.END, message + "\n")
                self.chat_area.config(state='disabled')
                self.chat_area.yview(tk.END)
            except:
                messagebox.showerror("Disconnected", "Connection lost!")
                self.client_socket.close()
                self.root.quit()
                break

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Username and password cannot be empty.")
            return

        try:
            self.client_socket.send(f"LOGIN:{username}:{password}".encode("utf-8"))
            response = self.client_socket.recv(1024).decode("utf-8")

            if response == "LOGIN_SUCCESS":
                self.username = username
                self.create_chat_screen()
            elif response == "LOGIN_FAIL":
                messagebox.showerror("Error", "Login failed! Invalid credentials.")
            elif response == "ALREADY_LOGGED_IN":
                messagebox.showerror("Error", "This account is already logged in.")
            else:
                messagebox.showerror("Error", "Unexpected server response.")
        except:
            messagebox.showerror("Error", "Connection lost while logging in!")

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Username and password cannot be empty.")
            return

        try:
            self.client_socket.send(f"REGISTER:{username}:{password}".encode("utf-8"))
            response = self.client_socket.recv(1024).decode("utf-8")

            if response == "REGISTER_SUCCESS":
                messagebox.showinfo("Success", "Registration successful! You can now log in.")
            elif response == "REGISTER_FAIL":
                messagebox.showerror("Error", "Username already exists.")
            else:
                messagebox.showerror("Error", "Unexpected server response.")
        except:
            messagebox.showerror("Error", "Connection lost while registering!")

if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
