import os
import socket
import sys

coordinator_conn = None
my_port = None  # Global variable to store the port

def set_connection_to_coordinator():
    global coordinator_conn  # Declare coordinator_conn as global
    print(f"Waiting for coordinator connection...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 12345))
    server_socket.listen(1)
    conn, client_address = server_socket.accept()
    print(f"Coordinator connected: {client_address}")
    coordinator_conn = conn

def set_connection_to_client():
    global my_port  # Ensure that my_port is used in this function
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if my_port is None:
        print("Port not set!")
        return  # Exit if the port is not set

    server_socket.bind(('0.0.0.0', my_port))  # Use the dynamic port here
    server_socket.listen(1)
    print(f"Waiting for client connection on port {my_port}...")
    conn, client_address = server_socket.accept()
    print(f"Connected with client {client_address}")
    message = conn.recv(1024).decode('utf-8')
    print(f"Received message from client: {message}")
    conn.close()

def list_files(directory):
    try:
        response = ""
        files = os.listdir(directory)
        for i, file in enumerate(files):
            file_path = os.path.join(directory, file)
            validity = calculate_file_validity(file_path)
            response += f"{i+1}. {file} ({validity}%)\n"
        return response
    except Exception as e:
        return f"Error accessing {directory}: {e}"

def get_file_metadata(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
        meta = lines[0].split(" ")
        return [m.split("-") for m in meta]
    
def get_file_size(file_path):
    with open(file_path, 'r') as f:
        return sum(len(line) for line in f.readlines()[1:])

def calculate_file_validity(file_path):
    with open(file_path, 'r') as f:
        data_sum = 0
        touples = get_file_metadata(file_path)
        file_size = get_file_size(file_path)
        for t in touples:
            data_sum += int(t[1])
        return int((data_sum/file_size)*100)

def do_i_have_file(directory, file_name):
    files = os.listdir(directory)
    return "YES" if file_name in files else "NO"
        

def main():
    global my_port  # Ensure to refer to the global variable
    print("Server Started")

    # Set the port from command-line argument
    if len(sys.argv) < 2:
        print("Port argument is required!")
        return  # Exit if port argument is missing
    
    my_port = int(sys.argv[1])  # Get port from the command-line argument
    print(f"Server listening on port: {my_port}")
    
    set_connection_to_coordinator() 
    server_folder = os.getenv("SERVER_FOLDER", "/data")

    try:
        while True:
            data = coordinator_conn.recv(1024).decode('utf-8')
            print(f"Received command: {data}")
            if data == "list":
                files = list_files(server_folder)
                coordinator_conn.sendall(files.encode('utf-8'))
            elif data == "connect":
                coordinator_conn.sendall("OK".encode('utf-8'))
            elif data == "connect_to_client":
                set_connection_to_client()
            elif len(data.lower().split()) == 2 and data.lower().split()[0] == "do_you_have":
                response = do_i_have_file(server_folder, data.lower().split(" ")[1])
                coordinator_conn.sendall(response.encode('utf-8'))
            else:
                coordinator_conn.sendall("Unknown command".encode('utf-8'))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        coordinator_conn.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
