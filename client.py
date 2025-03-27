import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, StringVar, OptionMenu

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Client")
        
        self.username = None
        self.HOST = None
        self.PORT = 12345
        
        self.setup_connection()
    
    def setup_connection(self):
        # Connection setup dialog
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
        
        # Create login frame
        login_frame = tk.Frame(self.root)
        login_frame.pack(padx=20, pady=20)
        
        tk.Label(login_frame, text="Username:").grid(row=0, column=0, sticky='e')
        self.username_entry = tk.Entry(login_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(login_frame, text="Password:").grid(row=1, column=0, sticky='e')
        self.password_entry = tk.Entry(login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Buttons frame
        buttons_frame = tk.Frame(login_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        tk.Button(buttons_frame, text="Login", command=self.login).grid(row=0, column=0, padx=5)
        tk.Button(buttons_frame, text="Register", command=self.register).grid(row=0, column=1, padx=5)
    
    def create_chat_screen(self):
        self.clear_window()
        
        # Chat area
        self.chat_area = scrolledtext.ScrolledText(self.root, state='disabled', height=20)
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Message and send frame
        message_frame = tk.Frame(self.root)
        message_frame.pack(padx=10, pady=5, fill=tk.X)
        
        # Group selection
        self.group_var = StringVar(value="Global")
        tk.Label(message_frame, text="Group:").pack(side=tk.LEFT)
        self.group_dropdown = OptionMenu(message_frame, self.group_var, ["Global"])
        self.group_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Recipient for DM
        tk.Label(message_frame, text="Send To:").pack(side=tk.LEFT)
        self.recipient_entry = tk.Entry(message_frame, width=15)
        self.recipient_entry.pack(side=tk.LEFT, padx=5)
        
        # Message entry
        self.msg_entry = tk.Entry(message_frame, width=40)
        self.msg_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.msg_entry.bind('<Return>', lambda event: self.send_message())
        
        # Send button
        tk.Button(message_frame, text="Send", command=self.send_message).pack(side=tk.LEFT, padx=5)
        
        # Create group button
        tk.Button(self.root, text="Create Group", command=self.create_group).pack(pady=5)
        
        # Start receiving messages
        threading.Thread(target=self.receive_messages, daemon=True).start()
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def send_message(self):
        recipient = self.recipient_entry.get()
        group = self.group_var.get()
        message = self.msg_entry.get().strip()
        
        if not message:
            return
        
        try:
            if group and group != "Select Group":
                # Send to group
                self.client_socket.send(f"MSG:GROUP:{group}:{message}".encode("utf-8"))
            elif recipient:
                # Send Direct Message
                self.client_socket.send(f"MSG:DM:{recipient}:{message}".encode("utf-8"))
            else:
                # Send to Global chat
                self.client_socket.send(f"MSG:Global:Global:{message}".encode("utf-8"))
            
            # Clear message entry
            self.msg_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Send Error", str(e))
    
    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode("utf-8")
                if not message:
                    break
                
                # Handle different types of server messages
                if message.startswith("UPDATE_GROUPS:"):
                    groups = message.split(":")[1:]
                    self.update_group_dropdown(groups)
                else:
                    self.update_chat_area(message)
            
            except Exception as e:
                messagebox.showerror("Receive Error", str(e))
                break
        
        # If we break out of the loop, attempt to reconnect
        self.reconnect()
    
    def update_chat_area(self, message):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)
    
    def update_group_dropdown(self, groups):
        menu = self.group_dropdown["menu"]
        menu.delete(0, "end")
        for group in groups:
            menu.add_command(label=group, command=lambda value=group: self.group_var.set(value))
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Input Error", "Username and password cannot be empty.")
            return
        
        try:
            self.client_socket.send(f"LOGIN:{username}:{password}".encode("utf-8"))
            
            response = self.client_socket.recv(1024).decode("utf-8")
            
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
            messagebox.showerror("Login Error", str(e))
    
    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Input Error", "Username and password cannot be empty.")
            return
        
        try:
            self.client_socket.send(f"REGISTER:{username}:{password}".encode("utf-8"))
            
            response = self.client_socket.recv(1024).decode("utf-8")
            
            if response == "REGISTER_SUCCESS":
                messagebox.showinfo("Registration Successful", "You can now log in")
            elif response == "REGISTER_FAIL":
                messagebox.showerror("Registration Failed", "Username already exists")
            else:
                messagebox.showerror("Error", "Unexpected server response.")
        
        except Exception as e:
            messagebox.showerror("Registration Error", str(e))
    
    def create_group(self):
        group_name = simpledialog.askstring("Create Group", "Enter group name:")
        
        if group_name:
            try:
                self.client_socket.send(f"CREATE_GROUP:{group_name}".encode("utf-8"))
                
                response = self.client_socket.recv(1024).decode("utf-8")
                
                if response.startswith("GROUP_CREATED:"):
                    messagebox.showinfo("Group Created", f"Group '{group_name}' created successfully!")
                else:
                    messagebox.showerror("Group Creation Failed", "Could not create group.")
            
            except Exception as e:
                messagebox.showerror("Group Creation Error", str(e))
    
    def reconnect(self):
        # Attempt to reconnect
        messagebox.showinfo("Disconnected", "Lost connection to server. Reconnecting...")
        self.root.after(0, self.setup_connection)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("600x700")  # Set a default window size
    client = ChatClient(root)
    root.mainloop()