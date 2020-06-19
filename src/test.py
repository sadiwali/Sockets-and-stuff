import network
import usocket as socket
import uselect
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('ww5.0', '0066f650q')

while not sta_if.isconnected():
    pass

a = socket.getaddrinfo('192.168.0.15', 5000)[0][-1]
s = socket.socket()
poller = uselect.poll()
poller.register(s.connect(a), uselect.POLLIN)
res = poller.poll(1000)
if not res:
    print("timed out")
else:
    print(str(res))

