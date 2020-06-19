from machine import Pin
import ujson as json
import urequests as requests
import network
import utime as time
import sys
import usocket as socket
import _thread as thread


WIFI_CONFIG = "wifi_config.json"
MY_ID = "23"  # id will be unique
sta_if = None  # the station interface
ap_if = None  # the access point interface

SERVER_PORT = '5000'
led = Pin(2, Pin.OUT)

# read the json config
config = {}


def load_config():
    global config
    try:
        with open(WIFI_CONFIG, 'r') as f:
            config = json.load(f)
        print("opened config " + str(config))
    except Exception as e:
        print("NO CONFIG FILE!")
        raise Exception(e)


def save_config():
    global config
    try:
        print("writing config file...")
        with open(WIFI_CONFIG, 'w') as f:
            json.dump(config, f)
        print("wrote config to file.")
    except:
        print("Could not save config")


def get_ip():
    return sta_if.ifconfig()[0]


def setup_handshake_server():
    '''
    Create a 'server' for the actual server to ping and connect to.
    The result of this function will give the correct server ip.
    '''
    global config
   # listen for the registration request from server
    addr = socket.getaddrinfo('0.0.0.0', SERVER_PORT)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(addr)
    s.listen(1)
    print('listening on', addr)
    sent_ok = False
    try:
        while True:
            # try to accept a client
            cl, addr = s.accept()
            while True:
                # client accepted, listen to client
                msg = cl.recv(1024)
                if len(msg) <= 0:
                    print("looking for a new client...")
                    break
                msg = msg.decode('utf-8').split(' ').strip()

                if msg[0] == "HANDSHAKE":
                    # found server
                    print("Connection from " + str(cl) + ", " + str(addr) + "!")
                    cl.send(bytes('200 OK', 'utf-8'))
                    print("sent ok, listening for response")
                    sent_ok = True
                elif (msg.decode('utf-8') == "200 OK" and sent_ok):
                    # server acknowledged
                    cl.close()
                    s.close()
                    print(
                        "Found the new server ip via handshake! It is: " + addr[0])
                    config['server_ip'] = str(addr[0])
                    is_registered = True
                    led.on()
                    time.sleep(1)
                    led.off()
                    save_config()
                    print("Registered to the server successfully!")
                    return True
                elif (msg.decode('utf-8' == "400 BAD")):
                    print("Looking for new connection")
                    cl.close()
                    break
                else:
                    print("got garbage, looking for new client")
                    cl.close()
                    break

    except Exception as e:
        print("exception here: " + str(e))
        s.close()
        raise


def setup_client():
    try:
        addr = socket.getaddrinfo(config['server_ip'], 4000)[0][-1]
        s = socket.socket()
        s.connect(addr)
        s.send(("HANDSHAKE " + MY_ID).encode('utf-8'))
        print("Started a client, connected to " + str(addr))
        while True:
            msg = s.recv(1024)
            if len(msg) <= 0:
                print("the server has said nothing. quitting...")
                break
            msg = msg.decode('utf-8').split(' ').strip()

            if (msg[0] == "STATUS"):
                if msg[1] == "200":
                    if msg[2] == "HANDSHAKE":
                        print("Server acknowledged handshake")
            elif msg[0] == "TEXT":
                pass
            elif msg[0] == "JSON":
                data = json.loads(msg[1])
        s.close()
    except Exception as e:
        print(str(e))
        print(
            "Got an error while connecting with that ip. Setting up to listen for server...")
        if not setup_handshake_server():
            print("something went wrong while listening for the server. Exiting")
            sys.exit()
        else:
            print("found the new working ip, trying to connect again.")
            setup_comms_client()


# main code
def start():
    global config
    global sta_if
    try:
        load_config()

        if ("ssid" not in config.keys()):
            print("The config file is corrupt!")
            raise Exception("config file is corrupt")

        sta_if = network.WLAN(network.STA_IF)

        if not sta_if.isconnected():
            print("connecting to wifi...")
            sta_if.active(True)
            sta_if.connect(config["ssid"], config["password"])
            while not sta_if.isconnected():
                pass
            print("wifi connected for first time!")
        else:
            print("already connected!")

        print("my ip is: " + get_ip())

    except Exception as e:
        print(e)
        print("acting as access point to get wifi data...")
        # act as wifi access point to get wifi info

    # sync my ip with server

    # setup a client thread to listen to server commands
    setup_comms_client()


# do the things
start()
