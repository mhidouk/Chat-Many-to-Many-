import socket
import threading
import random


class ChatServer:
    """TCP chat server that handles multiple client connections using threads."""
    
    def __init__(self, port=None):
        """Initialize the server with a given port or a random one."""
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = 'localhost'
        self.port = port if port else self._get_random_port()
        self.clients = {}  # {client_socket: nickname}

    def _get_random_port(self):
        """Return a random port between 1024 and 65535."""
        return random.randint(1024, 65535)

    def start(self):
        """Start the server and listen for incoming connections."""
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen()
        print(f"Server listening on {self.host}:{self.port}")

        while True:
            client, address = self.server_sock.accept()
            threading.Thread(
                target=self._handle_client,
                args=(client,),
                daemon=True
            ).start()

    def _handle_client(self, client):
        """Handle messages from a connected client."""
        nickname = client.recv(1024).decode('ascii')
        self.clients[client] = nickname
        print(f"{nickname} connected")
        self._broadcast(f"{nickname} joined the chat!", sender_client=client)

        try:
            while True:
                message = client.recv(1024).decode('ascii')
                if not message:
                    break
                self._broadcast(f"{nickname}: {message}", sender_client=client)
        except ConnectionError:
            pass
        finally:
            self._remove_client(client)
            client.close()

    def _broadcast(self, message, sender_client=None):
        """Send a message to all clients except the sender."""
        for client in self.clients:
            if client != sender_client:
                try:
                    client.send(f"{message}\n".encode('ascii'))
                except ConnectionError:
                    self._remove_client(client)

    def _remove_client(self, client):
        """Remove a disconnected client and notify others."""
        if client in self.clients:
            nickname = self.clients[client]
            del self.clients[client]
            self._broadcast(f"{nickname} left the chat.")


class ChatClient:
    """TCP chat client that connects to a server and sends/receives messages."""
    
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.nickname = None

    def start(self, host, port):
        """Connect to the server at the given host and port."""
        self.sock.connect((host, port))
        self.connected = True
        print(f"Connected to {host}:{port}")
        threading.Thread(
            target=self._receive_messages,
            daemon=True
        ).start()

    def _receive_messages(self):
        """Listen for incoming messages from the server."""
        while self.connected:
            try:
                data = self.sock.recv(1024).decode('ascii')
                print(data)
            except ConnectionError:
                break
        print("\nDisconnected.")
        self.connected = False
        self.sock.close()

    def send_message(self, message):
        """Send a message to the server if connected."""
        if self.connected:
            try:
                self.sock.sendall(message.encode('ascii'))
            except ConnectionError:
                self.disconnect()

    def disconnect(self):
        """Close the connection to the server."""
        if self.connected:
            self.connected = False
            self.sock.close()

    def _handle_command(self, command):
        """Process user commands."""
        if command.startswith("send"):
            _, message = command.split(" ", 1)
            self.send_message(f"{self.nickname}: {message}")
        elif command == "disconnect":
            self.disconnect()
        elif command == "exit":
            self.disconnect()
            print("Exiting the client.")
            exit()
        elif command.startswith("connect"):
            _, new_host, new_port = command.split(" ", 2)
            self.start(new_host, int(new_port))
        else:
            print("Unknown command")


def main():
    """Run either a server or client based on user input."""
    role = input("Enter 'server' or 'client': ").lower()

    if role == 'server':
        port_input = input("Enter server port (leave empty for random port): ").strip()
        port = int(port_input) if port_input else None
        chat_server = ChatServer(port)
        chat_server.start()

    elif role == 'client':
        chat_client = ChatClient()
        host = input("Enter server IP: ")
        port = int(input("Enter server port: "))
        chat_client.start(host, port)
        chat_client.nickname = input("Enter your nickname: ")

        while chat_client.connected:
            user_input = input("Enter your command: ")
            chat_client._handle_command(user_input)

    else:
        print("Invalid role. Enter 'server' or 'client'.")


if __name__ == "__main__":
    main()
