import network
import machine
import time

# wlan access
ssid_ = ""
wpa2_pass = ""

## ftp access
#from ftp import ftpserver

def do_connect():
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(ssid_, wpa2_pass)
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())

do_connect()