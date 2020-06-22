
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

    # Camera resilience - if we fail to init try to deinit and init again
    if (not camera.init()):
        camera.deinit()
        await asyncio.sleep(1)
        # If we fail to init, return a 503

        if app_config['camera'] == 'ESP32-CAM':
            if(not camera.init(0, format=camera.JPEG)):  # ESP32-CAM
                yield from picoweb.start_response(resp, status=503)
                yield from resp.awrite('ERROR: Failed to initialise camera\r\n\r\n')
                return

        elif app_config['camera'] == 'M5CAMERA':
            if (not camera.init(0, d0=32, d1=35, d2=34, d3=5, d4=39, d5=18, d6=36, d7=19,
                    href=26, vsync=25, reset=15, sioc=23, siod=22, xclk=27, pclk=21)):   #M5CAMERA  
                yield from picoweb.start_response(resp, status=503)
                yield from resp.awrite('ERROR: Failed to initialise camera\r\n\r\n')
                return

    # wait for sensor to start and focus before capturing image
    await asyncio.sleep(2)
    buf = camera.capture()

    led.off()
    camera.deinit()

    if type(buf) is bytes and len(buf) > 0:
        yield from picoweb.start_response(resp, "image/jpeg")
        yield from resp.awrite(buf)
    else:
        picoweb.http_error(resp, 503)


def run():
    app.run(host='0.0.0.0', port=80, debug=True)
