# uPyCam - Streaming 
This repository includes an application example to stream video using MicroPython on the:
* [ESP32-CAM](https://bit.ly/2Ndn8tN)
* [M5Camera](https://bit.ly/317Xb74)

Using a browser, you can connect to the boards to see the video stream. 

## Timelapse
The boards can be used as portable timelapse cameras. Check out this repository for more code: [lemariva/uPyCam branch timelapse-camera](https://github.com/lemariva/uPyCam/tree/timelapse-camera)

## Firmware
The MicroPython firmware was extended to add camera support. The firmware is located in this repository: [lemariva/micropython-camera-driver](https://github.com/lemariva/micropython-camera-driver).

Follow these articles to get more information:
* [MicroPython: Support for cameras: M5CAMERA, ESP32-CAM etc.](https://lemariva.com/blog/2020/06/micropython-support-cameras-m5camera-esp32-cam-etc)
* [MicroPython: M5CAMERA timelapse over MQTT](https://lemariva.com/blog/2020/06/micropython-m5camera-timelapse-over-mqtt)

Note: If they are not available, they will be published in the next days.

## Web-browser
You can choose between a photo or streaming mode:
* Photo mode: `http://<<board-ip>>`
* Streaming mode: `http://<<board-ip>>/?stream=true`

Streaming mode added by [Krayon](https://github.com/krayon/upyesp32cam/commit/8b63edec50dca9416bb4b2b75207ac53788c597a). Thanks! 
