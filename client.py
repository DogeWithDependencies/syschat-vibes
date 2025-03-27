import socket
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
import threading

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Client")
        
        self.username = None
        self.client_socket = None
        
        # Ask user to select the server IP
        self.server_ip = simpledialog.askstring("Server IP", "Enter server IP (e.g., 127.0.0.1):")
        self.server_port = 12345
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            self.client_socket.connect((self.server_ip, self.server_port))
            self.create_login_screen()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {e}")
            self.root.quit()
    
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
        
        self.chat_area = scrolledtext.ScrolledText(self.root, state='disabled')
        self.chat_area.pack(padx=10, pady=10)
        
        self.msg_entry = tk.Entry(self.root)
        self.msg_entry.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(self.root, text="Send", command=self.send_message).pack()
        
        threading.Thread(target=self.receive_messages, daemon=True).start()
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def send_message(self):
        message = self.msg_entry.get()
        if message:
            self.client_socket.send(f"MSG:Global:{message}".encode("utf-8"))
            self.msg_entry.delete(0, tk.END)
    
    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode("utf-8")
                self.chat_area.config(state='normal')
                self.chat_area.insert(tk.END, message + "\n")
                self.chat_area.config(state='disabled')
                self.chat_area.yview(tk.END)
            except:
                break
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        self.client_socket.send(f"LOGIN:{username}:{password}".encode("utf-8"))
        response = self.client_socket.recv(1024).decode("utf-8")
        if response == "LOGIN_SUCCESS":
            self.username = username
            self.create_chat_screen()
        else:
            messagebox.showerror("Login Failed", "Invalid credentials")
    
    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        self.client_socket.send(f"REGISTER:{username}:{password}".encode("utf-8"))
        response = self.client_socket.recv(1024).decode("utf-8")
        if response == "REGISTER_SUCCESS":
            messagebox.showinfo("Registration Successful", "You can now log in")
        else:
            messagebox.showerror("Registration Failed", "Username already exists")

if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
