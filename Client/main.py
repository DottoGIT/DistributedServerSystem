import socket
import sys
import threading

def connect_to_server(server_ip, port=12000):
    port += int(server_ip[-1])
    print(f"Connecting to {server_ip}:{port}")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_ip, port))
        print(f"Connected to {server_ip} on port {port}")
        message = "Hello, Server!"
        client_socket.sendall(message.encode('utf-8'))
        response = client_socket.recv(1024).decode('utf-8')
        print(f"Received from server: {response}")
    except Exception as e:
        print(f"Failed to connect to {server_ip} on port {port}: {e}")
    finally:
        print(f"Connection with {server_ip} closed")
        client_socket.close()

def start_server_threads(servers_with_file):
    threads = []
    for server_ip in servers_with_file:
        thread = threading.Thread(target=connect_to_server, args=(server_ip,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()

def handle_download(socket, file_name):
    """Handles download command from client to coordinator."""
    socket.sendall(f"download {file_name}".encode('utf-8'))
    info = socket.recv(1024).decode('utf-8')
    print(info)
    socket.sendall("OK".encode('utf-8'))
    servers_with_file = socket.recv(1024).decode('utf-8').split("\n")[:-1]
    print(servers_with_file)
    start_server_threads(servers_with_file)

def main():
    print("Client Started...")
    if len(sys.argv) < 2:
        print("Client needs server IP!")
        return
    
    server_ip = sys.argv[1]
    coordinator_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    coordinator_socket.connect((server_ip, 12345))
    print(f"Connection with coordinator established.\n")

    print("*---------------------------------------------*")
    print("|    Welcome to Distributed Server System!    |")
    print("*---------------------------------------------*")
    print(f"Type <help> to get avaiable commands from the coordinator")
    print(f"Type <exit> to quit the application\n")
    try:
        while True:
            command = input("Enter command: ")
            if command.lower() == 'exit':
                print("Goodbye.")
                break
            elif len(command.lower().split()) == 2 and command.lower().split()[0] == "download":
                print("\n----- Coordinator Response -----\n")
                handle_download(coordinator_socket, command.lower().split(" ")[1])
                print("--------------------------------")
            else:
                coordinator_socket.sendall(command.encode('utf-8'))
                data = coordinator_socket.recv(1024).decode('utf-8')
                print("\n----- Coordinator Response -----\n")
                print(data)
                print("--------------------------------")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        coordinator_socket.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
