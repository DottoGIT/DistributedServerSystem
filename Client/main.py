import socket
import sys
import threading

coordinator_socket = None
gathered_data = []
mutex = threading.Lock()

#-------------------------------------------------------------------------------#
#                            SERVER COMMUNICATION                               #
#-------------------------------------------------------------------------------#

def connect_to_server(server_ip, port=12000):
    port += int(server_ip[-1])
    try:
        print(f"Connecting to {server_ip}:{port}")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, port))
        print(f"Connected to {server_ip} on port {port}")
        while True:
            response = client_socket.recv(1024).decode('utf-8').split("@")
            if response == "finished":
                break
            print(f"Received from {server_ip}: {response[0]} at offset {int(response[1])}")
            with mutex:
                gathered_data.append(response)

    except Exception as e:
        print(f"{server_ip} on port {port} finished communication")
    finally:
        print(f"- Connection with {server_ip} closed -")
        client_socket.close()

def start_server_threads(servers_with_file):
    global gathered_data
    threads = []
    gathered_data.clear()
    for server_ip in servers_with_file:
        thread = threading.Thread(target=connect_to_server, args=(server_ip,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()

def handle_download(file_name):
    global coordinator_socket
    """Handles download command from client to coordinator."""
    coordinator_socket.sendall(f"download {file_name}".encode('utf-8'))
    info = coordinator_socket.recv(1024).decode('utf-8')
    print(info)
    coordinator_socket.sendall("OK".encode('utf-8'))
    servers_with_file = coordinator_socket.recv(1024).decode('utf-8')
    if servers_with_file == "None":
        print("No active server has requested file \n")
        return
    print(servers_with_file)
    start_server_threads(servers_with_file.split("\n")[:-1])
    print("--------------------------------\n\n")
    sorted_data = sorted(gathered_data, key=lambda x: int(x[1]))
    ready_message_str = "".join([item[0] for item in sorted_data])
    print(f"Gathered Data:\n{ready_message_str}")
    print(f"Data validity: {int(len(ready_message_str)/60*100)}%")


#-------------------------------------------------------------------------------#
#                                     MAIN                                      #
#-------------------------------------------------------------------------------#
def main():
    if len(sys.argv) < 2:
        print("Client needs server IP!")
        return
    
    print("Client Started...")
    server_ip = sys.argv[1]
    global coordinator_socket
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
            if command == 'exit':
                print("Goodbye.")
                break
            elif len(command.split()) == 2 and command.split()[0] == "download":
                print("\n----- Coordinator Response -----\n")
                handle_download(command.split(" ")[1])
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
