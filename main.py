"""
import webcam
webcam.run()
"""

import camera
import machine
from config import app_config
from webserver import webcam

server = webcam()
server.run(app_config)
