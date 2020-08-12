from flask import Flask
from flask import request
import json
import os.path
from os import path
import requests
import socket
import threading

SAVEFILE = "savefile.json"
SERVER_PORT = "5000"
app = Flask(__name__)

devices = {}
device_status = {}


class ClientThread(threading.Thread):
    def __init__(self, clientAddress, clientsocket):
        threading.Thread.__init__(self)
        self.cl = clientsocket
        self.clientAddress = clientAddress
        self.id = None
        print("new socket started for " + str(clientAddress))

    def run(self):
        msg = ''
        while True:
            msg = self.cl.recv(1024)
            if len(msg) <= 0:
                print("client thread " + str(self.clientAddress)+ " closing.")
                self.cl.close()
                break
            msg = msg.decode('utf-8').split(' ').strip()

            if msg[0] == "HANDSHAKE":
                id = msg[1]
                devices[id] = {"ip": self.clientAddress[0]}
                save_file()
                self.send("STATUS 200 " + msg[0]) # message read 
            elif msg[0] == "STATUS":
                pass

            

            
            if('ID' in msg):
                    msg_id = msg[msg.find('ID=')+3, len(msg)]
                    print("Setting my id to " + msg_id)
                    self.id = msg_id

            print("Message from client " + str(self.clientAddress) + ": " + msg)

    def send(self, data):
        self.cl.send(bytes(data, 'utf-8'))


class ServerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('0.0.0.0', 4000))
        self.connected_threads = []
        print("Server started")

    def run(self):
        try:
            while True:
                print("Listening for clients...")
                self.s.listen(1)
                cl, addr = self.s.accept()
                newthread = ClientThread(addr, cl)
                newthread.start()
                self.connected_threads.append(newthread)
        finally:
            self.s.close()

    def send(self, id, what):
        print("Sending: " + what + " to " + id)
        for i in self.connected_threads:
            if i.isAlive():
                if i.id and i.id == id:
                    i.send(what)
                    return True
        return False

    def end(self):
        self._is




def save_file():
    try:
        with open(SAVEFILE, 'w') as f:
            json.dump(devices, f)
    except:
        raise Exception("Can't save file...")


def load_file():
    global devices
    try:
        if (not path.exists(SAVEFILE)):
            save_file()
        else:
            with open(SAVEFILE, 'r') as f:
                devices = json.load(f)
    except:
        raise


@app.route('/get_devices', methods=['GET'])
def get_devices():
    return json.dumps(devices), 200


@app.route('/sync/<id>', methods=['GET'])
def sync(id):
    devices[id] = {"ip": request.remote_addr}
    save_file()
    print("Sync request from " + id + ", " + request.remote_addr)
    return json.dumps({'success': True, 'message': 'Added and saved to storage'}), 200


def find_devices():
    num_found = 0
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    print("HOST NAME IS: "+hostname + " MY IP IS: " + ip)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for i in range(19, 22):
        ip_to_try = ip[0:ip.rfind('.')+1]+str(i)
        if ip_to_try == ip:
            continue
        try:
            print("now trying ip: " + ip_to_try)
            c = socket.create_connection((ip_to_try, 5000), 5)
            c.send(bytes("HANDSHAKE", 'utf-8'))
            while True:
                msg = c.recv(1024)
                if len(msg) <= 0:
                    print("end of communication")
                    c.close()
                    break
                msg = msg.decode('utf-8').split(' ').strip()

                if msg[0] == "STATUS":
                    if msg[1] == "200" and msg[2] == "HANDSHAKE":
                        print("deice found at " + ip_to_try)
                        break
                elif('ID' in msg):
                    msg_id = msg[msg.find('ID=')+3, len(msg)]
                    devices[msg_id] = ip_to_try
                    print("device found at " + ip_to_try)
                    num_found += 1
                    save_file()

            print("Found " + str(num_found) + " devices so far...")
        except Exception as e:
            print(e)
    print("Device search completed! Found " +
          str(num_found) + " devices in total.")


def start_server():
    server_thread = ServerThread()
    server_thread.start()
    return server_thread


if __name__ == '__main__':
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    load_file()
    server = start_server()
    server.send("23", "bye")
    print("I can do other things now while server is working")

    # find_devices()
    app.run(host='0.0.0.0', port=5000)
