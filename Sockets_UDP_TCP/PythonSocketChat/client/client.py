import socket
import threading
import struct
import sys


SERVER_IP: str = '127.0.0.1'
SERVER_PORT: int = 12345
ADDR: tuple = (SERVER_IP, SERVER_PORT)

MULTICAST_GROUP: str = '224.0.0.224'
MULTICAST_PORT: int = 12346
MULTICAST_ADDR: tuple = (MULTICAST_GROUP, MULTICAST_PORT)

FORMAT: str = 'utf-8'
NICK: str = ''

ASCII_ART_UDP: str = """      
      /`·.¸
     /¸...¸`:·
 ¸.·´  ¸   `·.¸.·´)
: © ):´;      ¸  {
 `·.¸ `·  ¸.·´\`·¸)
     `\\\´´\¸.·´
"""

ASCII_ART_MULTICAST: str = """
      _   _
     /(   )\\
     \(   )/
   |/ \\\_//  \|
  /  (#) (#)  \\
  \  /     \  /
   \ \_____/ /
    \/  |  \/  
  _ | o | o | _
 | \|o  |  o|/ |
 |  |  o|o  |  |
/|\ |o  |  o| /|\\
    \  o|o  /
    /\__|__/\\
   /         \\
   \         /
   |\       /|
"""


client: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_udp: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_multicast: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def receive_tcp() -> None:
    while True:
        try:
            message = client.recv(1024).decode(FORMAT)
            if message == '#SERVER SHUTDOWN#':
                print("[CLIENT] Server has been shutdown. Press enter key to leave.")
                break
            print(message)
        except ConnectionAbortedError:
            break


def receive_udp() -> None:
    client_udp.sendto("UDP INIT".encode(FORMAT), ADDR)

    while True:
        try:
            message, _ = client_udp.recvfrom(1024)
            print(message.decode(FORMAT))
        except (KeyboardInterrupt, OSError):
            break


def receive_multicast() -> None:
    while True:
        try:
            message, _ = client_multicast.recvfrom(1024)
            print(message.decode(FORMAT))
        except (KeyboardInterrupt, OSError):
            break


def main() -> None:
    NICK = input("[CLIENT] Enter your nickname: ")

    try:
        client.connect(ADDR)
    except ConnectionRefusedError:
        print("[CLIENT] Could not connect to the server.")
        exit()
    
    client_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_udp.bind(client.getsockname())

    # settig up multicast socket
    client_multicast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    if sys.platform == "win32":
        client_multicast.bind(('', MULTICAST_PORT))
    else:
        client_multicast.bind(MULTICAST_ADDR)

    group = socket.inet_aton(MULTICAST_GROUP)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    client_multicast.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


    client.send(NICK.encode(FORMAT))

    receive_thread = threading.Thread(target=receive_tcp)
    receive_thread.start()

    receive_udp_thread = threading.Thread(target=receive_udp)
    receive_udp_thread.start()

    receive_multicast_thread = threading.Thread(target=receive_multicast)
    receive_multicast_thread.start()

    while True:
        try:
            input_message = input("")

            if input_message == 'Q':
                print("[CLIENT] Disconnecting...")
                break
            elif input_message == 'U':
                udp_msg = f'[{NICK}]:\n' + ASCII_ART_UDP
                client_udp.sendto(udp_msg.encode(FORMAT), ADDR)
            elif input_message == 'M':
                multicast_msg = f'[{NICK}]:\n' + ASCII_ART_MULTICAST
                client_multicast.sendto(multicast_msg.encode(FORMAT), MULTICAST_ADDR)
            elif input_message:
                input_message = f'[{NICK}] {input_message}'
                client.send(input_message.encode(FORMAT))
        except (KeyboardInterrupt, ConnectionResetError):
            print("[CLIENT] Disconnecting...")
            break

    client_udp.close()
    client_multicast.close()
    client.close()


if __name__ == '__main__':
    main()
