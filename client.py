import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, ttk

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
        self.user_list = []  # Stores available users
        self.group_list = []  # Stores available groups

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

        self.chat_area = scrolledtext.ScrolledText(self.root, state='disabled', height=15)
        self.chat_area.pack(padx=10, pady=10)

        tk.Label(self.root, text="Send To:").pack()

        # Dropdown for selecting users
        self.recipient_var = tk.StringVar()
        self.recipient_dropdown = ttk.Combobox(self.root, textvariable=self.recipient_var, state="readonly")
        self.recipient_dropdown.pack()

        # Dropdown for selecting groups
        tk.Label(self.root, text="Groups:").pack()
        self.group_var = tk.StringVar()
        self.group_dropdown = ttk.Combobox(self.root, textvariable=self.group_var, state="readonly")
        self.group_dropdown.pack()

        self.msg_entry = tk.Entry(self.root)
        self.msg_entry.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(self.root, text="Send", command=self.send_message).pack()
        tk.Button(self.root, text="Create Group", command=self.create_group).pack()
        tk.Button(self.root, text="Join Group", command=self.join_group).pack()

        # Start receiving messages
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def send_message(self):
        recipient = self.recipient_var.get()
        group = self.group_var.get()
        message = self.msg_entry.get()

        if not message:
            return

        if recipient:
            self.client_socket.send(f"MSG:DM:{recipient}:{message}".encode("utf-8"))
        elif group:
            self.client_socket.send(f"MSG:GROUP:{group}:{message}".encode("utf-8"))

        self.msg_entry.delete(0, tk.END)

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode("utf-8")
                if not message:
                    break

                if message.startswith("USER_LIST:"):
                    self.user_list = message.split(":")[1].split(",")
                    self.update_dropdowns()
                elif message.startswith("GROUP_LIST:"):
                    self.group_list = message.split(":")[1].split(",")
                    self.update_dropdowns()
                else:
                    self.chat_area.config(state='normal')
                    self.chat_area.insert(tk.END, message + "\n")
                    self.chat_area.config(state='disabled')
                    self.chat_area.yview(tk.END)
            except:
                break

    def update_dropdowns(self):
        self.recipient_dropdown["values"] = self.user_list
        self.group_dropdown["values"] = self.group_list

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        self.client_socket.send(f"LOGIN:{username}:{password}".encode("utf-8"))
        response = self.client_socket.recv(1024).decode("utf-8")
        if response == "LOGIN_SUCCESS":
            self.username = username
            self.create_chat_screen()
        else:
            messagebox.showerror("Login Failed", "Invalid credentials or already logged in.")

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
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
                self.group_list.append(group_name)
                self.update_dropdowns()
                messagebox.showinfo("Group Created", f"Group '{group_name}' created successfully!")

    def join_group(self):
        group_name = self.group_var.get()
        if group_name:
            self.client_socket.send(f"JOIN_GROUP:{group_name}".encode("utf-8"))
            response = self.client_socket.recv(1024).decode("utf-8")
            if response.startswith("JOINED_GROUP"):
                messagebox.showinfo("Joined Group", f"You joined '{group_name}'!")
            else:
                messagebox.showerror("Join Failed", "Could not join group.")

if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
