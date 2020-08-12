from utils import ThreadObject, ConfigHandler, NetworkHandler, ConnectionHandler
from machine import Pin




class Device:
    pins = {}

    @staticmethod
    def setup_pins():
        Device.setup_pin(2, "out")


    @staticmethod
    def setup_pin(pin, pintype):
        Device.pins[pin] = Pin(pin, Pin.IN if pintype.lower() == "in" else Pin.OUT)


    @staticmethod
    def set_high(pin):
        if not Device.pins[pin] or not Device.pins[pin].mode() == Pin.OUT:
            Device.setup_pin(pin, "out")
        if Device.pins[pin]:
            Device.pins[pin].on()
    
    @staticmethod
    def set_low(pin):
        if not Device.pins[pin] or not Device.pins[pin].mode() == Pin.OUT:
            Device.setup_pin(pin, "out")
        if Device.pins[pin]:
            Device.pins[pin].off()

    @staticmethod
    def process_commands(command):
        command = command.decode()
        print("Got command <" + str(command) +">")
        command = command.split(' ')
        if command[0] == "HANDSHAKE":
            pass
        elif command[0] == "200":
            pass
        elif command[0] == "TURNON":
            Device.set_high(int(command[1]))
        elif command[0] == "TURNOFF":
            Device.set_low(int(command[1]))
        else:
            print("Unknown command found: '" + str(command) +"'")


    @staticmethod
    def onboard_led(on):
        if on:
            Device.pins[2].on()
        else:
            Device.pins[2].off()
        
   
ConfigHandler.set_config_name("wifi_config.json")
ConfigHandler.load()
NetworkHandler.connect()
ConnectionHandler.find_server_ip()
Device.setup_pins()
ThreadObject(ConnectionHandler.listen(ConnectionHandler.get_server_addr, Device.process_commands)).start()