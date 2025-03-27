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
        self.selected_recipient = "Global"  # Default message recipient (Global chat)
        
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
        
        # Display chat area
        self.chat_area = scrolledtext.ScrolledText(self.root, state='disabled', height=15, width=50)
        self.chat_area.pack(padx=10, pady=10)
        
        # Message recipient selection (dropdown)
        self.recipient_label = tk.Label(self.root, text=f"Send to: {self.selected_recipient}")
        self.recipient_label.pack(pady=5)
        
        self.recipient_var = tk.StringVar(self.root)
        self.recipient_var.set(self.selected_recipient)  # Set default recipient
        
        self.recipient_dropdown = tk.OptionMenu(self.root, self.recipient_var, "Global", "DM", "Group1", "Group2")
        self.recipient_dropdown.pack(pady=5)
        
        self.msg_entry = tk.Entry(self.root)
        self.msg_entry.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(self.root, text="Send", command=self.send_message).pack()

        # Start listening for incoming messages
        threading.Thread(target=self.receive_messages, daemon=True).start()

        # Update recipient dynamically based on dropdown selection
        self.recipient_var.trace("w", self.update_recipient)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def update_recipient(self, *args):
        """Update recipient based on the dropdown selection."""
        self.selected_recipient = self.recipient_var.get()
        self.recipient_label.config(text=f"Send to: {self.selected_recipient}")

    def send_message(self):
        message = self.msg_entry.get()
        if message:
            # Send message based on the selected recipient (Global, DM, Group)
            if self.selected_recipient == "Global":
                self.client_socket.send(f"MSG:Global:{message}".encode("utf-8"))
            elif self.selected_recipient == "DM":
                # Send to a specific user (should be done after selecting a user)
                target_user = simpledialog.askstring("Direct Message", "Enter the username of the recipient:")
                if target_user:
                    self.client_socket.send(f"MSG:DM:{target_user}:{message}".encode("utf-8"))
            elif self.selected_recipient.startswith("Group"):
                group_name = self.selected_recipient
                self.client_socket.send(f"MSG:GROUP:{group_name}:{message}".encode("utf-8"))
            self.msg_entry.delete(0, tk.END)

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode("utf-8")
                if message:
                    self.chat_area.config(state='normal')
                    self.chat_area.insert(tk.END, f"{message}\n")
                    self.chat_area.config(state='disabled')
            except:
                break

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username and password:
            self.client_socket.send(f"LOGIN:{username}:{password}".encode("utf-8"))
            response = self.client_socket.recv(1024).decode("utf-8")
            if response == "LOGIN_SUCCESS":
                self.username = username
                self.create_chat_screen()
            elif response.startswith("LOGIN_FAIL"):
                messagebox.showerror("Login Error", "Login failed!")

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username and password:
            self.client_socket.send(f"REGISTER:{username}:{password}".encode("utf-8"))
            response = self.client_socket.recv(1024).decode("utf-8")
            if response == "REGISTER_SUCCESS":
                messagebox.showinfo("Success", "Registration successful! Please log in.")
            else:
                messagebox.showerror("Registration Error", "Username already exists.")

    def close(self):
        if self.client_socket:
            self.client_socket.close()

if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
