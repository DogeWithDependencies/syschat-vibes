import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Client")
        
        self.username = None
        self.HOST = simpledialog.askstring("Server IP", "Enter the server IP address:")
        self.PORT = 12345
        
        if not self.HOST:
            messagebox.showerror("Error", "Server IP is required!")
            root.destroy()
            return
        
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_server()
        
        self.create_login_screen()
    
    def connect_to_server(self):
        try:
            self.client_socket.connect((self.HOST, self.PORT))
        except Exception as e:
            messagebox.showerror("Connection Failed", f"Could not connect to server: {e}")
            self.root.destroy()
    
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
        
        self.recipient_label = tk.Label(self.root, text="Send To:")
        self.recipient_label.pack()
        self.recipient_entry = tk.Entry(self.root)
        self.recipient_entry.pack()
        
        self.group_label = tk.Label(self.root, text="Select Group:")
        self.group_label.pack()
        self.group_dropdown = tk.OptionMenu(self.root, tk.StringVar(), [])
        self.group_dropdown.pack()
        
        self.msg_entry = tk.Entry(self.root)
        self.msg_entry.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(self.root, text="Send", command=self.send_message).pack()
        tk.Button(self.root, text="Create Group", command=self.create_group).pack()
        
        threading.Thread(target=self.receive_messages, daemon=True).start()
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def send_message(self):
        recipient = self.recipient_entry.get()
        group = self.group_dropdown.get()
        message = self.msg_entry.get()
        if recipient and message:
            if group != "Select Group":  # Send to group
                self.client_socket.send(f"MSG:GROUP:{group}:{message}".encode("utf-8"))
            else:  # Send to recipient
                self.client_socket.send(f"MSG:DM:{recipient}:{message}".encode("utf-8"))
            self.msg_entry.delete(0, tk.END)
    
    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode("utf-8")
                if not message:
                    break
                print(f"Received message: {message}")  # Log received messages
                if message.startswith("UPDATE_GROUPS:"):
                    groups = message.split(":")[1:]
                    self.update_group_dropdown(groups)
                else:
                    self.chat_area.config(state='normal')
                    self.chat_area.insert(tk.END, message + "\n")
                    self.chat_area.config(state='disabled')
                    self.chat_area.yview(tk.END)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break
    
    def update_group_dropdown(self, groups):
        menu = self.group_dropdown["menu"]
        menu.delete(0, "end")
        for group in groups:
            menu.add_command(label=group, command=lambda group=group: self.group_dropdown.set(group))
        self.group_dropdown.set("Select Group")
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Input Error", "Username and password cannot be empty.")
            return
        self.client_socket.send(f"LOGIN:{username}:{password}".encode("utf-8"))
        
        try:
            response = self.client_socket.recv(1024).decode("utf-8")
            print(f"Server response to login: {response}")  # Log server response
            
            if response == "LOGIN_SUCCESS":
                self.username = username
                self.create_chat_screen()
            elif response == "LOGIN_FAIL":
                messagebox.showerror("Login Failed", "Invalid credentials.")
            elif response == "ALREADY_LOGGED_IN":
                messagebox.showerror("Login Failed", "You are already logged in elsewhere.")
            else:
                messagebox.showerror("Error", "Unexpected server response.")
        except Exception as e:
            messagebox.showerror("Error", f"Error while logging in: {e}")
    
    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Input Error", "Username and password cannot be empty.")
            return
        self.client_socket.send(f"REGISTER:{username}:{password}".encode("utf-8"))
        
        try:
            response = self.client_socket.recv(1024).decode("utf-8")
            if response == "REGISTER_SUCCESS":
                messagebox.showinfo("Registration Successful", "You can now log in")
            elif response == "REGISTER_FAIL":
                messagebox.showerror("Registration Failed", "Username already exists")
            else:
                messagebox.showerror("Error", "Unexpected server response.")
        except Exception as e:
            messagebox.showerror("Error", f"Error while registering: {e}")
    
    def create_group(self):
        group_name = simpledialog.askstring("Create Group", "Enter group name:")
        if group_name:
            self.client_socket.send(f"CREATE_GROUP:{group_name}".encode("utf-8"))
            try:
                response = self.client_socket.recv(1024).decode("utf-8")
                if response.startswith("GROUP_CREATED"):
                    messagebox.showinfo("Group Created", f"Group '{group_name}' created successfully!")
                else:
                    messagebox.showerror("Group Creation Failed", "Could not create group.")
            except Exception as e:
                messagebox.showerror("Error", f"Error while creating group: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
