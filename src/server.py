from utils import ThreadObject, ConfigHandler, NetworkHandler, ConnectionHandler
import socket
SERVER_PORT = "4000"

devices = {}
device_status = {}


if __name__ == '__main__':
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    #ConfigHandler.set_config_name("config.json")
    #ConfigHandler.load()




    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    c_addr = None
    sock.bind(('0.0.0.0', 4000))
    while True:
        data, addr = sock.recvfrom(1024)
        data = data.decode()
        print(data + "\n")
        if data == "HANDSHAKE":
            c_addr = addr
            sock.sendto("200 OK".encode(), addr)
            break



    while True:    
        g = input("Enter command: ")
        sock.sendto(g.encode(), addr)

