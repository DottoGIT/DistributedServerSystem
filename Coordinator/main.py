# Example TCP coordinator

import socket

CHUNK_SIZE = 5
server_ips = ["server_1", "server_2", "server_3"]
server_connections = [None, None, None]
client_conn = None
client_address = None

#-------------------------------------------------------------------------------#
#                             CONNECTION MANAGEMENT                             #
#-------------------------------------------------------------------------------#

def set_connection_to_client():
    global client_conn
    global client_address
    result = "Waiting for connection with client...\n"
    coordinator_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    coordinator_socket.bind(('0.0.0.0', 12345))
    coordinator_socket.listen(1)
    client_temp, client_address_temp = coordinator_socket.accept()
    client_conn = client_temp
    client_address = client_address_temp
    result += f"Client connected: {client_address}"
    return result


def set_connections_to_servers(excpt = []):
    global client_address
    response = ""
    for i, server_ip in enumerate(server_ips):
        response += server_ip + ": "
        if server_ip in excpt:
            response += "OK\n"
            continue
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.settimeout(0.5)
            server_socket.connect((server_ip, 12345))
            answer = send_command_to_server("connect", server_socket)
            if answer == "OK":
                server_connections[i] = server_socket
                response += "OK\n"
        except:
            server_connections[i] = None
            response += "ERROR\n"
    return response

#-------------------------------------------------------------------------------#
#                        COMMUNICATION WITH SERVERS                             #
#-------------------------------------------------------------------------------#

def send_command_to_server(command, conn):
    try:
        conn.sendall(command.encode('utf-8'))
        response = conn.recv(1024).decode('utf-8')
        return response
    except Exception as e:
        return "Server Unreachable"

#-------------------------------------------------------------------------------#
#                              CLIENT COMMANDS                                  #
#-------------------------------------------------------------------------------#

def help_command():
    global client_conn
    print(f"Command <help> recieved")
    response = "Available Commands:\n"
    response += "1. list: List files stored in servers\n"
    response += "2. status: Check servers availability\n"
    response += "2. download <file_name>: download files from servers simultaneously\n"
    client_conn.sendall(response.encode('utf-8'))

def list_command():
    print(f"Command <list> recieved")
    response = "Servers Storage: \n"
    for i, connection in enumerate(server_connections):
        server_response = send_command_to_server("list", connection)
        if connection != None:
            response += f"--- server_{i+1} ---\n{server_response}"
    client_conn.sendall(response.encode('utf-8'))


def download_command(file_name):
    print(f"Command <download> recieved")

    # Inform about active servers with file
    response = f"Starting {file_name} download...\nServers that contain file:\n"
    client_conn.sendall(response.encode('utf-8'))
    client_conn.recv(1024).decode('utf-8')

    response = ""
    for i, server_connection in enumerate(server_connections):
        if send_command_to_server(f"do_you_have {file_name}", server_connection) == "YES":
            response += f"{server_ips[i]}\n"
            send_command_to_server(f"connect_to_client", server_connection)
    client_conn.sendall(response.encode('utf-8'))

    if response == "":
        return

    # Begin Downloading
    print(f"Managing servers...")

    print(f"Download completed")

def status_command():
    print(f"Command <status> recieved")
    active_servers = []
    response = "Server Status: \n"
    for i, server_ip in enumerate(server_ips):
        if send_command_to_server("connect", server_connections[i]) == "OK":
            active_servers.append(server_ip)
    response += set_connections_to_servers(excpt=active_servers)

    client_conn.sendall(response.encode('utf-8'))


def unknown_command():
    print(f"Command <unknown> recieved")
    response = "Unknown command\n"
    client_conn.sendall(response.encode('utf-8'))

#-------------------------------------------------------------------------------#
#                                  MAIN                                         #
#-------------------------------------------------------------------------------#

def main():
    print("Coordinator Started")

    result = set_connection_to_client()
    print(result)
    result = set_connections_to_servers()
    print(result)

    while(True):
        data = client_conn.recv(1024).decode('utf-8')
        if data == "help":
            help_command()
        elif data == "list":
            list_command()
        elif len(data.lower().split()) == 2 and data.lower().split()[0] == "download":
            download_command(data.lower().split(" ")[1])
        elif data == "status":
            status_command()
        else:
            unknown_command()

if __name__ == "__main__":
    main()