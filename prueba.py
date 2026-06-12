import network
import socket
import time
import uasyncio as asyncio
import dht
import machine
import ujson
import urequests
import pandas

from machine import Pin
from machine import ADC
from Libraries.simple import MQTTClient

# =========================
# TESTEO
# =========================
led_integrado = Pin("LED", Pin.OUT)
led_integrado.on()
time.sleep(3)
led_integrado.off()

# =========================
# IDENTIDAD
# =========================
SERIAL = "001"
HOSTNAME = "raspberrytr-" + SERIAL

# =========================
# LEDS WIFI / MQTT / REGISTRO
# =========================
led_wifi_verde = Pin(16, Pin.OUT)
led_wifi_rojo = Pin(17, Pin.OUT)

led_mqtt_verde = Pin(18, Pin.OUT)
led_mqtt_rojo = Pin(19, Pin.OUT)

led_registro_verde = Pin(12, Pin.OUT)
led_registro_rojo = Pin(13, Pin.OUT)

# =========================
# BOTÓN
# =========================
boton = Pin(20, Pin.IN, Pin.PULL_UP)

# =========================
# SENSORES
# =========================
dht_sensor = dht.DHT11(Pin(21))
mq5 = ADC(Pin(26))

# =========================
# VARIABLES
# =========================
temperatura = 0
humedad = 0
co2 = 0

mqtt_client = None
mqtt_conectado = False

# =========================
# ARCHIVOS
# =========================
AP_SSID = "PicoW_Config"
AP_PASSWORD = "configuracion"

SSID_FILE = "connections/ssid.txt"
PASSWORD_FILE = "connections/password.txt"
BROKER_FILE = "connections/broker.txt"
PUERTO_FILE = "connections/port.txt"
DNS_FILE = "connections/dns.txt"

HTML_FILE = "resources/pages/configuracion.html"
DESPEDIDA_FILE = "resources/pages/despedida.html"

# =========================
# UTILIDADES
# =========================
def leer_archivo(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except:
        return ""

def guardar_config(ssid, password, broker, puerto, dns):
    with open(SSID_FILE, "w") as f:
        f.write(ssid)

    with open(PASSWORD_FILE, "w") as f:
        f.write(password)

    with open(BROKER_FILE, "w") as f:
        f.write(broker)

    with open(PUERTO_FILE, "w") as f:
        f.write(puerto)

    with open(DNS_FILE, "w") as f:
        f.write(dns)

def obtener_parametro(url, nombre):
    try:
        query = url.split("?")[1]
        for p in query.split("&"):
            k, v = p.split("=")
            if k == nombre:
                return v.replace("+", " ")
    except:
        pass
    return ""

def pagina_html():
    html = leer_archivo(HTML_FILE)

    html = html.replace("{{SSID}}", leer_archivo(SSID_FILE).strip())
    html = html.replace("{{PASSWORD}}", leer_archivo(PASSWORD_FILE).strip())
    html = html.replace("{{BROKER}}", leer_archivo(BROKER_FILE).strip())
    html = html.replace("{{PUERTO}}", leer_archivo(PUERTO_FILE).strip())
    html = html.replace("{{DNS}}", leer_archivo(DNS_FILE).strip())

    return html

# =========================
# SENSORES
# =========================
def leer_sensores():
    global temperatura, humedad, co2

    try:
        dht_sensor.measure()
        temperatura = dht_sensor.temperature()
        humedad = dht_sensor.humidity()
    except Exception as e:
        print("Error DHT11:", e)

    try:
        valor = mq5.read_u16()
        co2 = int((valor * 500) / 65535)
    except Exception as e:
        print("Error MQ5:", e)

# =========================
# REGISTRO
# =========================
def registrar_dispositivo(ip, dns):

    max_intentos = 3
    intento = 0

    while intento < max_intentos:

        intento += 1

        try:
            
            
            url = (
                "http://{}:5221/Registro/Registrar"
                "?serie={}&ip={}"
            ).format(dns, SERIAL, ip)

            print(f"Enviando registro POST ({intento}/{max_intentos})")
            print("URL:", url)

            r = urequests.get(url)

            print("STATUS:", r.status_code)
            print("HEADERS:", r.headers)

            resp = r.text

            print("RESP:", repr(resp))

            r.close()

            

            print("Respuesta:", resp)

            if "OK" in resp:

                led_registro_verde.on()
                led_registro_rojo.off()

                print("Registro OK")

                return True

        except Exception as e:

            print("Error registro:", e)

        led_registro_verde.off()
        led_registro_rojo.on()

        if intento < max_intentos:
            time.sleep(3)

    print("Todos los intentos fallaron")

    return False

# =========================
# AP MODE
# =========================
__ap = network.WLAN(network.AP_IF)
__ap.active(True)
__ap.config(essid=AP_SSID, password=AP_PASSWORD)

while not __ap.active():
    time.sleep(1)

print("AP iniciado:", AP_SSID)
print("IP AP:", __ap.ifconfig()[0])

# =========================
# CONFIG SERVER
# =========================
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(addr)
server.listen(1)
server.settimeout(1)

config_guardada = False

while not config_guardada:

    try:
        client, addr = server.accept()
    except:
        continue

    try:
        request = client.recv(1024).decode()
        url = request.split(" ")[1]

        print("CONFIG HTTP:", url)

        if url.startswith("/guardar"):

            ssid = obtener_parametro(url, "ssid")
            password = obtener_parametro(url, "password")
            broker = obtener_parametro(url, "broker")
            puerto = obtener_parametro(url, "puerto")
            dns = obtener_parametro(url, "dns")

            print("Guardando configuración...")
            guardar_config(ssid, password, broker, puerto, dns)

            html = leer_archivo(DESPEDIDA_FILE)

            client.sendall(("HTTP/1.1 200 OK\r\n\r\n" + html).encode())
            time.sleep(0.4)

            config_guardada = True

        else:
            html = pagina_html()
            client.sendall(("HTTP/1.1 200 OK\r\n\r\n" + html).encode())

    except Exception as e:
        print("Error web config:", e)

    finally:
        try:
            client.close()
        except:
            pass

server.close()
__ap.active(False)

print("CONFIG SERVER cerrado")

# =========================
# WIFI STA
# =========================
ssid = leer_archivo(SSID_FILE).strip()
pwd = leer_archivo(PASSWORD_FILE).strip()
dns = leer_archivo(DNS_FILE).strip()

def conectar_wifi():

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    network.hostname(HOSTNAME)

    if not wlan.isconnected():

        print("Conectando WiFi...")
        led_wifi_rojo.on()
        led_wifi_verde.off()

        wlan.connect(ssid, pwd)

        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            print(".", end="")
            time.sleep(1)
            timeout -= 1

    if wlan.isconnected():

        ip = wlan.ifconfig()[0]

        print("\nWiFi conectado")
        print("IP:", ip)

        led_wifi_verde.on()
        led_wifi_rojo.off()

        # REGISTRO OBLIGATORIO - BLOQUEANTE HASTA COMPLETAR
        registro_exitoso = False
        while not registro_exitoso:
            if registrar_dispositivo(ip, dns):
                registro_exitoso = True
            else:
                print("Reintentando registro completo en 5 segundos...")
                time.sleep(5)

        return wlan

    print("WiFi fallo")
    led_wifi_rojo.on()
    led_wifi_verde.off()
    return None

# =========================
# TASK SENSORES
# =========================
async def task_sensores():
    while True:
        leer_sensores()
        await asyncio.sleep(2)

# =========================
# TASK HTTP (ENDPOINTS)
# =========================
async def task_http():

    addr = socket.getaddrinfo("0.0.0.0", 8080)[0][-1]
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(addr)
    server.listen(5)
    server.settimeout(0.2)

    print("HTTP SERVER iniciado en puerto 8080")
    print("Endpoints listos:")
    print(" - /temperatura")
    print(" - /humedad")
    print(" - /co2")

    while True:

        try:
            client, addr = server.accept()
        except:
            await asyncio.sleep(0.05)
            continue

        try:
            request = client.recv(1024).decode()
            url = request.split(" ")[1]

            print("HTTP REQUEST:", url)

            if url == "/temperatura":
                body = str(temperatura)
            elif url == "/humedad":
                body = str(humedad)
            elif url == "/co2":
                body = str(co2)
            else:
                body = "404"

            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                "Connection: close\r\n"
                "\r\n" + body
            )

            client.sendall(response.encode())

        except Exception as e:
            print("HTTP error:", e)

        finally:
            try:
                client.close()
            except:
                pass

        await asyncio.sleep(0.05)

# =========================
# TASK MQTT
# =========================
async def task_mqtt():

    global mqtt_client, mqtt_conectado

    while True:

        try:

            wlan = network.WLAN(network.STA_IF)

            if not wlan.isconnected():
                print("WiFi OFF -> MQTT OFF")
                mqtt_conectado = False
                led_mqtt_rojo.on()
                led_mqtt_verde.off()
                await asyncio.sleep(2)
                continue

            if not mqtt_conectado:

                broker = leer_archivo(BROKER_FILE).strip()
                puerto = int(leer_archivo(PUERTO_FILE).strip() or 1883)

                print("Conectando MQTT...")

                mqtt_client = MQTTClient(HOSTNAME.encode(), broker, puerto)
                mqtt_client.connect()

                mqtt_client.publish((HOSTNAME + "/prueba").encode(), b"prueba")

                mqtt_conectado = True
                led_mqtt_rojo.off()
                led_mqtt_verde.on()

                print("MQTT conectado")

            mqtt_client.publish((HOSTNAME + "/co2").encode(), str(co2).encode())
            print("MQTT CO2:", co2)
            await asyncio.sleep_ms(100)

            mqtt_client.publish((HOSTNAME + "/temperatura").encode(), str(temperatura).encode())
            await asyncio.sleep_ms(100)

            mqtt_client.publish((HOSTNAME + "/humedad").encode(), str(humedad).encode())
            print("MQTT enviado")

        except Exception as e:

            print("MQTT error:", e)

            mqtt_conectado = False
            led_mqtt_verde.off()
            led_mqtt_rojo.on()

            try:
                if mqtt_client:
                    mqtt_client.disconnect()
            except:
                pass

            mqtt_client = None

            await asyncio.sleep(2)

        await asyncio.sleep(2)

# =========================
# MAIN
# =========================
async def main():
    await asyncio.gather(
        task_sensores(),
        task_http(),
        task_mqtt()
    )

# =========================
# LOOP PRINCIPAL
# =========================
while True:

    wifi = conectar_wifi()

    if wifi is None:
        time.sleep(5)
        continue

    print("Sistema completamente iniciado")

    try:
        asyncio.run(main())
    except Exception as e:
        print("Async error:", e)

        try:
            if mqtt_client:
                mqtt_client.disconnect()
        except:
            pass

        mqtt_client = None
        mqtt_conectado = False

        time.sleep(5)