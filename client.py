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
        self.client_socket = None

        self.users = ["Global"]  # Store users for DM
        self.groups = ["Global"]  # Store available groups

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

        tk.Label(message_frame, text="Send To:").pack(side=tk.LEFT)
        self.recipient_var = StringVar(value="Global")
        self.recipient_dropdown = OptionMenu(message_frame, self.recipient_var, *self.users)
        self.recipient_dropdown.pack(side=tk.LEFT, padx=5)

        tk.Label(message_frame, text="Group:").pack(side=tk.LEFT)
        self.group_var = StringVar(value="Global")
        self.group_dropdown = OptionMenu(message_frame, self.group_var, *self.groups)
        self.group_dropdown.pack(side=tk.LEFT, padx=5)

        self.msg_entry = tk.Entry(message_frame)
        self.msg_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.msg_entry.bind('<Return>', lambda event: self.send_message())

        tk.Button(message_frame, text="Send", command=self.send_message).pack(side=tk.RIGHT)

        tk.Button(self.root, text="Create Group", command=self.create_group).pack(pady=5)

        threading.Thread(target=self.receive_messages, daemon=True).start()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def send_message(self):
        recipient = self.recipient_var.get()
        group = self.group_var.get()
        message = self.msg_entry.get().strip()
        
        if not message:
            return

        try:
            if group and group != "Global":
                self.client_socket.send(f"MSG:GROUP:{group}:{message}".encode("utf-8"))
            elif recipient and recipient != "Global":
                self.client_socket.send(f"MSG:DM:{recipient}:{message}".encode("utf-8"))
            else:
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

                if message.startswith("UPDATE_USERS:"):
                    self.update_users(message.split(":")[1:])
                elif message.startswith("UPDATE_GROUPS:"):
                    self.update_groups(message.split(":")[1:])
                else:
                    self.chat_area.config(state='normal')
                    self.chat_area.insert(tk.END, message + "\n")
                    self.chat_area.config(state='disabled')
                    self.chat_area.yview(tk.END)
            except:
                messagebox.showerror("Disconnected", "Connection lost!")
                self.root.quit()
                break

    def update_users(self, users):
        self.users = ["Global"] + users
        menu = self.recipient_dropdown["menu"]
        menu.delete(0, "end")
        for user in self.users:
            menu.add_command(label=user, command=lambda value=user: self.recipient_var.set(value))

    def update_groups(self, groups):
        self.groups = ["Global"] + groups
        menu = self.group_dropdown["menu"]
        menu.delete(0, "end")
        for group in self.groups:
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

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("600x700")
    client = ChatClient(root)
    root.mainloop()
