# Integrated modules
from machine import Pin
from time import sleep
# Models
from drivers.led_estado import LedEstado
# Services
import services.access_point_service as ap

# Datos Estaticos
NUMERO_SERIE = "001"
HOSTNAME = f"sensor-tr-{NUMERO_SERIE}"

# Inicializar hardware
led_internet = LedEstado(False, 15, 14)
led_servidor = LedEstado(False, 10, 9)
boton = Pin(0, Pin.IN, Pin.PULL_DOWN)





# Encender access point para configuracion
ap.iniciar_ap(HOSTNAME)
config_guardada = False
while not config_guardada:
    ap.recibir_cliente()
    sleep(0.05)
    if boton.value() == 1 or ap.config_guardada():
        config_guardada = True

ap.cerrar_ap()