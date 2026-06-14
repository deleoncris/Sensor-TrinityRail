# Integrated modules
from machine import Pin
from time import sleep
from json import load
import asyncio

# Models
from drivers.led_estado import LedEstado
from drivers.sensor_dht11 import SensorDHT11
from drivers.sensor_mq5 import SensorMQ5
# Services
import services.access_point_service as ap
import services.wifi_conecction_service as wifi
import services.server_conecction_service as server

# Datos Estaticos
NUMERO_SERIE = "001"
HOSTNAME = f"sensor-tr-{NUMERO_SERIE}"

# Variables
token : str = None

# Inicializar hardware
led_internet = LedEstado(False, 17, 16)
led_servidor = LedEstado(False, 19, 18)
dht11 = SensorDHT11(21)
mq5 = SensorMQ5(26)
boton = Pin(20, Pin.IN, Pin.PULL_DOWN)

# Iniciar Access Point para configuracion
ap.iniciar_ap(HOSTNAME)
config_guardada = False
while not config_guardada:
    ap.recibir_cliente()
    if boton.value() == 1 or ap.config_guardada():
        config_guardada = True
ap.cerrar_ap()

# Conectar a WiFi
with open("resources/config.json", "r") as f:
    config = load(f)
async def conectar_wifi():
    await wifi.conectar(HOSTNAME, config.get("ssid"), config.get("password"), led_internet)

# Comunicarse con el servidor
async def conectarse_servidor():
    await server.registrarse(NUMERO_SERIE, led_servidor)

# Enviar datos cada minuto
async def mandar_datos():
    while True:
        if wifi.conectado() and server.conectado():
            th = dht11.datos()
            if th == None:
                print("Error en dht")
                # Envio Datos Unicamente por debug
                # Envio Datos Unicamente por debug
                # Envio Datos Unicamente por debug
                server.mandar_datos("30", "30", mq5.valor())
                # Envio Datos Unicamente por debug
                # Envio Datos Unicamente por debug
                # Envio Datos Unicamente por debug
            else:
                server.mandar_datos(th.get("temperatura"), th.get("humedad"), mq5.valor())
        await asyncio.sleep(60)


# Metodo Main para ejecutar el flujo de trabajo de forma asyncrona
async def main():
    # Crear tareas
    tarea_wifi = asyncio.create_task(conectar_wifi())
    await asyncio.sleep(10)
    tarea_server = asyncio.create_task(conectarse_servidor())
    tarea_datos = asyncio.create_task(mandar_datos())

    # Mantener el loop vivo manualmente
    while True:
        await asyncio.sleep(1)


try:
    asyncio.run(main())
except AttributeError:
    # Si asyncio.run no existe, usar este método:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())