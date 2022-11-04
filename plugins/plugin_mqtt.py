# mqtt plugin
# author: Sergey Pushkarev

import paho.mqtt.client as ph_mqtt
from vacore import VACore
import os

modname = os.path.basename(__file__)[:-3]

def start(core:VACore):
    manifest = {
        "name": "MQTT плагин",
        "version": "1.0",
        "require_online": False,

        "default_options":{ # Данные для подключения к брокеру mqtt
            "MQTT_CLIENTID": "Irine_voice",
            "MQTT_IP": "example.com",
            "MQTT_USER": "username",
            "MQTT_PASS": "password",
            "MQTT_PORT": "1883",
            "MQTT_TOPIC": "/Assistant",
            
            "devices":{ # Список устройств, значение - топик устройства (для чайника будет формироваться так: "/Assistant/u_01")
                'чайник': 'u_01',
                'свет в гостиной': 'u_02',
                'лампа': 'u_03',
            },
        },

        "commands": { # набор скиллов. Фразы скилла разделены | . Если найдены - вызывается функция
            "включи": mqtt_switch_on,
            "выключи": mqtt_switch_off,
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict): # создаст core.mqtt_clien для отправки данных
    options = manifest["options"]
    core.mqtt_client = ph_mqtt.Client(options["MQTT_CLIENTID"])
    core.mqtt_client.username_pw_set(options["MQTT_USER"], options["MQTT_PASS"])
    core.mqtt_client.connect(options["MQTT_IP"], int(options["MQTT_PORT"]))



def check_connect(core:VACore): # при обрыве подключения - переподключиться
    if not core.mqtt_client.is_connected():
        core.mqtt_client.connect(core.plugin_options(modname)["MQTT_IP"], core.plugin_options(modname)["MQTT_PORT"])



def mqtt_switch_on(core: VACore, phrase:str): # отправляет "1" в топик названного устройства
    check_connect(core)
    if phrase in core.plugin_options(modname)["devices"]:
        topic = f'{core.plugin_options(modname)["MQTT_TOPIC"]}/{core.plugin_options(modname)["devices"][phrase]}'
        result = core.mqtt_client.publish(topic, "1")
        if result[0] == 0:
            core.say(f'{phrase} включен')
        else:
            core.say(f'Ошибка {phrase} не включен')
    else:
        core.say(f'Нет устройства {phrase}')


def mqtt_switch_off(core: VACore, phrase:str): # отправляет "0" в топик названного устройства
    check_connect(core)
    if phrase in core.plugin_options(modname)["devices"]:
        topic = f'{core.plugin_options(modname)["MQTT_TOPIC"]}/{core.plugin_options(modname)["devices"][phrase]}'
        result = core.mqtt_client.publish(topic, "0")
        if result[0] == 0:
            core.say(f'{phrase} выключен')
        else:
            core.say(f'Ошибка {phrase} не выключен')
    else:
        core.say(f'Нет устройства {phrase}')



