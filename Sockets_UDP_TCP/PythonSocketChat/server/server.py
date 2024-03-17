import socket
import threading
import select

FORMAT: str = 'utf-8'
SERVER_IP: str = '127.0.0.1'
SERVER_PORT: int = 12345
ADDR: tuple = (SERVER_IP, SERVER_PORT)

connected_clients: set = set()
udp_clients: set = set()
connection_lock: threading.Lock = threading.Lock()

server_tcp: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_udp: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def broadcast_tcp(client: tuple, message: str) -> None:
    with connection_lock:
        for c in connected_clients:
            if c != client:
                c[1].send(message.encode(FORMAT))


def handle_tcp(client: socket.socket, address: tuple) -> None:
    nickname = client.recv(1024).decode(FORMAT)
    new_client = (nickname, client, address)
    people_in_the_room = "[CLIENT] Chatroom: "
    with connection_lock:
        for nick, _, __ in connected_clients:
            people_in_the_room += f'({nick}) '
        connected_clients.add(new_client)
    
    print(f"[SERVER] Connected with {nickname} {address}")
    broadcast_tcp(new_client, f"[{nickname}] Joined the chat.")
    client.send(people_in_the_room.encode(FORMAT))

    while True:
        try:
            message = client.recv(1024).decode(FORMAT)
            broadcast_tcp(new_client, message)
        except ConnectionResetError:
            with connection_lock:
                connected_clients.remove(new_client)
            
            print(f"[SERVER] {nickname} {address} disconnected.")
            broadcast_tcp(new_client, f"[{nickname}] Left the chat.")
            break
        except ConnectionAbortedError:
            break 


def handle_udp(client: tuple, message: bytes):
    if message.decode(FORMAT) == "UDP INIT":
        print("[SERVER] UDP INIT")
        udp_clients.add(client)
    else:
        print("[SERVER] UDP message.")
        with connection_lock:
            for cl in udp_clients:
                server_udp.sendto(message, cl)


def close_server() -> None:
    with connection_lock:
        for client in connected_clients:
            client[1].send("#SERVER SHUTDOWN#".encode(FORMAT))
            client[1].close()
        
    connected_clients.clear()
    udp_clients.clear()


def main() -> None:
    server_tcp.bind(ADDR)
    server_tcp.listen()
    server_udp.bind(ADDR)

    sockets = [server_tcp, server_udp]

    print("[SERVER] Starting the server...")
    while True:
        try:
            socks, _, _ = select.select(sockets, [], [], 1)

            for sock in socks:
                if sock == server_tcp:
                    client, address = server_tcp.accept()
                    tcp_thread = threading.Thread(target=handle_tcp, args=(client, address))
                    tcp_thread.start()  

                elif sock == server_udp:
                    data, address = server_udp.recvfrom(1024)
                    udp_thread = threading.Thread(target=handle_udp, args=(address, data))
                    udp_thread.start()
        except KeyboardInterrupt:
            print("[SERVER] Shutting down the server...")
            close_server()
            break
    
    server_tcp.close()
    server_udp.close()



if __name__ == '__main__':
    main()
