
import camera
import picoweb
import machine
import time
import uasyncio as asyncio
from config import *

led = machine.Pin(app_config['led'], machine.Pin.OUT)
app = picoweb.WebApp('app')

import ulogging as logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('app')

@app.route('/')
def index(req, resp):

    # parse query string
    req.parse_qs()
    flash = req.form.get('flash', 'false')
    if flash == 'true':
        led.on()
    stream = req.form.get('stream', 'false')
    stream = True if stream == 'true' else False
        
    # Camera resilience - if we fail to init try to deinit and init again
    if app_config['camera'] == 'ESP32-CAM':
        if (not camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)):
            camera.deinit()
            await asyncio.sleep(1)
            # If we fail to init, return a 503
            if (not camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)):  
                yield from picoweb.start_response(resp, status=503)
                yield from resp.awrite('ERROR: Failed to initialise camera\r\n\r\n')
                return
    elif app_config['camera'] == 'M5CAMERA':
        if (not camera.init(0, d0=32, d1=35, d2=34, d3=5, d4=39, d5=18, d6=36, d7=19,
                    href=26, vsync=25, reset=15, sioc=23, siod=22, xclk=27, pclk=21, fb_location=camera.PSRAM)):
            camera.deinit()
            await asyncio.sleep(1)
            # If we fail to init, return a 503
            if (not camera.init(0, d0=32, d1=35, d2=34, d3=5, d4=39, d5=18, d6=36, d7=19,
                    href=26, vsync=25, reset=15, sioc=23, siod=22, xclk=27, pclk=21, fb_location=camera.PSRAM)):   #M5CAMERA  
                yield from picoweb.start_response(resp, status=503)
                yield from resp.awrite('ERROR: Failed to initialise camera\r\n\r\n')
                return

    # wait for sensor to start and focus before capturing image
    await asyncio.sleep(2)
    
    n_frame = 0

    while True:
        n_try = 0
        buf = False
        while (n_try < 10 and buf == False): #{
            # wait for sensor to start and focus before capturing image
            buf = camera.capture()
            if (buf == False): await asyncio.sleep(2)
            n_try = n_try + 1
    

        if (not stream):
            led.off()
            camera.deinit()
    

        if (type(buf) is bytes and len(buf) > 0):
            try:
                if (not stream):
                    yield from picoweb.start_response(resp, "image/jpeg")
                    yield from resp.awrite(buf)
                    print('JPEG: Output frame')
                    break
            

                if (n_frame == 0): 
                    yield from picoweb.start_response(resp, "multipart/x-mixed-replace; boundary=myboundary")
            

                yield from resp.awrite('--myboundary\r\n')
                yield from resp.awrite('Content-Type:   image/jpeg\r\n')
                yield from resp.awrite('Content-length: ' + str(len(buf)) + '\r\n\r\n')
                yield from resp.awrite(buf)

            except:
                # Connection gone?
                print('Connection closed by client')
                led.off()
                camera.deinit()
                return

        else: 
            if (stream):
                led.off()
                camera.deinit()
        

            #picoweb.http_error(resp, 503)
            yield from picoweb.start_response(resp, status=503)
            if (stream and n_frame > 0): 
                yield from resp.awrite('Content-Type:   text/html; charset=utf-8\r\n\r\n')
            
            yield from resp.awrite('Issues:\r\n\r\n' + str(buf))
            return
        

        print('MJPEG: Output frame ' + str(n_frame))
        n_frame = n_frame + 1
    


def run():
    app.run(host='0.0.0.0', port=80, debug=True)
