import os
import socket
import sys

coordinator_conn = None
client_conn = None
server_socket = None
my_port = None
server_folder = None

#-------------------------------------------------------------------------------#
#                        COORDINATOR COMMUNICATION                              #
#-------------------------------------------------------------------------------#

def set_connection_to_coordinator():
    global coordinator_conn
    print(f"Waiting for coordinator connection...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 12345))
    server_socket.listen(1)
    conn, client_address = server_socket.accept()
    print(f"Coordinator connected: {client_address}")
    coordinator_conn = conn


def do_i_have_file(file_name):
    global server_folder
    files = os.listdir(server_folder)
    if file_name in files:
        file_path = os.path.join(server_folder, file_name)
        file_size = get_file_size(file_path)
        return f"YES {file_size}"
    else:
        return "NO"

def send_fragment_to_client(data):
    global server_folder
    file_name = data[0]
    offset = int(data[1])
    file_path = os.path.join(server_folder, file_name)

    if do_i_have_file(file_name) == "NO":
        return "File not found"
    
    if offset >= get_file_size(file_path):
        return "Wrong offset or data length"
    
    length = 0
    closest_offset = 0
    meta_data = get_file_metadata(file_path)
    for i in range(len(meta_data)):
        if offset >= int(meta_data[i][0]) and offset <= int(meta_data[i][0])-1 + int(meta_data[i][1]):
            length = int(meta_data[i][1]) - (offset - int(meta_data[i][0]))
            break
        # Check if offset is in boundries of meta data
        if i == 0 and offset < int(meta_data[i][0]):
            closest_offset = int(meta_data[i][0])
            break
        if i == len(meta_data)-1:
            closest_offset = get_file_size(file_path)+1
            break
        if offset > int(meta_data[i][0])-1 + int(meta_data[i][1]) and offset < int(meta_data[i+1][0]):
            closest_offset = int(meta_data[i+1][0])
            break
    
    if length > 0:
        with open(file_path, 'r') as f:
                first_line = f.readline()
                adjusted_offset = offset + len(first_line)
                f.seek(adjusted_offset, 0)
                client_response = f.read(length)
                coordinator_response = f"OK {length}"
    else:
        client_response = ""
        coordinator_response = f"NO {closest_offset}"
    
    print(f"sending client response: {client_response}")
    print(f"sending coord response: {coordinator_response}")
    return (client_response, coordinator_response, offset)


#-------------------------------------------------------------------------------#
#                            CLIENT COMMUNICATION                               #
#-------------------------------------------------------------------------------#

def open_client_communiaction():
    global server_socket
    global client_conn
    client_conn, client_address = server_socket.accept()
    print(f"Connected with client {client_address}")

def close_client_communication():
    global client_conn
    client_conn.sendall("finished".encode('utf-8'))
    client_conn.close()
    print("connection closed")

def set_port_for_to_client():
    global my_port
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', my_port))
    server_socket.listen(1)
    print(f"Waiting for client connection on port {my_port}...")

#-------------------------------------------------------------------------------#
#                              FILES MANAGEMENT                                 #
#-------------------------------------------------------------------------------#

def list_files():
    global server_folder
    try:
        response = ""
        files = os.listdir(server_folder)
        for i, file in enumerate(files):
            file_path = os.path.join(server_folder, file)
            validity = calculate_file_validity(file_path)
            response += f"{i+1}. {file} ({validity}%)\n"
        return response
    except Exception as e:
        return f"Error accessing {server_folder}: {e}\n"

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

#-------------------------------------------------------------------------------#
#                                   MAIN                                        #
#-------------------------------------------------------------------------------#

def main():
    global my_port
    global client_conn
    global server_folder
    print("Server Started")

    if len(sys.argv) < 2:
        print("Port argument is required!")
        return
    
    my_port = int(sys.argv[1])
    print(f"Server listening on port: {my_port}")
    
    set_connection_to_coordinator() 
    server_folder = os.getenv("SERVER_FOLDER", "/data")
    set_port_for_to_client()

    try:
        while True:
            data = coordinator_conn.recv(1024).decode('utf-8')
            print(f"Received command: {data}")
            if data == "list":
                files = list_files()
                coordinator_conn.sendall(files.encode('utf-8'))
            elif data == "connect":
                coordinator_conn.sendall("OK".encode('utf-8'))
            elif data == "connect_to_client":
                open_client_communiaction()
            elif data == "close_client_connection":
                close_client_communication()
            elif len(data.split()) == 3 and data.split()[0] == "send_fragment":
                response = send_fragment_to_client(data.split(" ")[1:])
                if response[0] != "":
                    client_conn.sendall((response[0] + "@" + str(response[2])).encode('utf-8'))
                coordinator_conn.sendall(response[1].encode('utf-8'))

            elif len(data.split()) == 2 and data.split()[0] == "do_you_have":
                response = do_i_have_file(data.split(" ")[1])
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
