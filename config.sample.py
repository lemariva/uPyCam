# Copyright 2020 LeMaRiva|tech lemariva.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

app_config = {
    'sleep-ms': 2000,
    'max-error': 10,
    'ftp': False,
    'mode': 'MQTT', # mode -> 'MQTT' or 'microSD'
    'camera': 'M5CAMERA',  # camera -> 'ESP32-CAM' or 'M5CAMERA'
    'led': 14, # led -> 4: ESP32-CAM or 14: M5CAMERA
}

mqtt_config = {
    'server': '192.168.178.147',
    'client_id': 'esp32-camera',
    'topic': b'Image'
}

microsd_config = {
    'miso':2,
    'mosi':15,
    'ss':13,
    'sck':14,
}


wifi_config = {
    'ssid':'',
    'password':''
}
