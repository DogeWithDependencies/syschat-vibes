import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog

HOST = "127.0.0.1"
PORT = 12345

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Client")
        
        self.username = None
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((HOST, PORT))
        
        self.create_login_screen()
    
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
        tk.Button(self.root, text="Create Group", command=self.create_group).pack()
        tk.Button(self.root, text="Join Group", command=self.join_group).pack()
        tk.Button(self.root, text="User List", command=self.get_user_list).pack()
        
        tk.Label(self.root, text="Chat Target (User/Group):").pack()
        self.chat_target_entry = tk.Entry(self.root)
        self.chat_target_entry.pack()
        self.chat_target_entry.insert(0, "Global")
        
        threading.Thread(target=self.receive_messages, daemon=True).start()
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def send_message(self):
        message = self.msg_entry.get().strip()
        target = self.chat_target_entry.get().strip()
        if message and target:
            self.client_socket.send(f"MSG:{target}:{message}".encode("utf-8"))
            self.msg_entry.delete(0, tk.END)
    
    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode("utf-8")
                if message.startswith("USERLIST:"):
                    users = message.split(":", 1)[1]
                    messagebox.showinfo("Users Online", users)
                else:
                    self.chat_area.config(state='normal')
                    self.chat_area.insert(tk.END, message + "\n")
                    self.chat_area.config(state='disabled')
                    self.chat_area.yview(tk.END)
            except:
                break
    
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showerror("Login Failed", "Fields cannot be empty.")
            return
        self.client_socket.send(f"LOGIN:{username}:{password}".encode("utf-8"))
        response = self.client_socket.recv(1024).decode("utf-8")
        if response == "LOGIN_SUCCESS":
            self.username = username
            self.create_chat_screen()
        else:
            messagebox.showerror("Login Failed", "Invalid credentials")
    
    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showerror("Registration Failed", "Username and password cannot be empty.")
            return
        self.client_socket.send(f"REGISTER:{username}:{password}".encode("utf-8"))
        response = self.client_socket.recv(1024).decode("utf-8")
        if response == "REGISTER_SUCCESS":
            messagebox.showinfo("Registration Successful", "You can now log in")
        else:
            messagebox.showerror("Registration Failed", "Username already exists")
    
    def create_group(self):
        group_name = simpledialog.askstring("Create Group", "Enter group name:")
        if group_name:
            self.client_socket.send(f"CREATE_GROUP:{group_name}".encode("utf-8"))
            response = self.client_socket.recv(1024).decode("utf-8")
            if response.startswith("GROUP_CREATED"):
                messagebox.showinfo("Success", f"Group '{group_name}' created.")
            else:
                messagebox.showerror("Error", "Group creation failed.")
    
    def join_group(self):
        group_name = simpledialog.askstring("Join Group", "Enter group name:")
        if group_name:
            self.client_socket.send(f"JOIN_GROUP:{group_name}".encode("utf-8"))
            response = self.client_socket.recv(1024).decode("utf-8")
            if response.startswith("JOINED_GROUP"):
                messagebox.showinfo("Success", f"Joined group '{group_name}'.")
            else:
                messagebox.showerror("Error", "Group does not exist.")
    
    def get_user_list(self):
        self.client_socket.send("USERLIST".encode("utf-8"))
        
if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
