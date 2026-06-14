import network
import asyncio

from drivers.led_estado import LedEstado

__wlan: network.WLAN = network.WLAN(network.STA_IF)
__wlan.active(True)
__intentar_conexion: bool = False

def conectado():
    return __wlan.isconnected()

async def conectar(hostname: str, ssid: str, password: str, led_estado: LedEstado):
    global __wlan, __intentar_conexion
    if not __intentar_conexion:
        __intentar_conexion = True
        while True:
            if not __wlan.isconnected():
                network.hostname(hostname)
                led_estado.mostrar_error()  # Rojo ON, Verde OFF
                __wlan.connect(ssid, password)
                # Esperar conexión con timeout
                timeout = 20
                while timeout > 0 and not __wlan.isconnected():
                    await asyncio.sleep(1)
                    timeout -= 1
                if __wlan.isconnected():
                    led_estado.mostrar_exito()  # Rojo OFF, Verde ON
                else:
                    led_estado.mostrar_error()  # Rojo ON, Verde OFF
                    await asyncio.sleep(5)
            else:
                # Ya está conectado, asegurar LED en éxito
                led_estado.mostrar_exito()  # Rojo OFF, Verde ON
                await asyncio.sleep(10)