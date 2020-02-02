import machine, sdcard, os
import ntptime
import time
import camera
from ftp import ftpserver

#import webcam
#webcam.run()

# camera init
led = machine.Pin(4, machine.Pin.OUT)
camera.init()
# sd mount
try:
    spi = machine.SPI(1, baudrate=100000, phase=0, polarity=0, sck=machine.Pin(14), mosi=machine.Pin(15), miso=machine.Pin(2)) 
    sd = sdcard.SDCard(spi, machine.Pin(13))
    os.mount(sd, '/sd')
    os.listdir('/')
except:
    machine.reset()

# ntp sync for date
ntptime.settime()
rtc = machine.RTC()

# ftp for checking
u = ftpserver()
u.start_thread()

error_counter = 0
while True:
    try:
        # prepare for photo
        led.value(1)
        led.value(0)
        time.sleep_ms(100)

        # take photo
        buf = camera.capture()
        time.sleep_ms(100)
        # save photo
        timestamp = rtc.datetime()
        time_str = '%4d%02d%02d%02d%02d%02d' %(timestamp[0], timestamp[1], timestamp[2], timestamp[4], timestamp[5], timestamp[6])
        f = open('sd/'+time_str+'.jpg', 'w')
        f.write(buf)
        time.sleep_ms(100)
        f.close()

        # sleep
        time.sleep_ms(2000)
    except:
        error_counter = error_counter + 1
        if error_counter > 10:
            machine.reset()
