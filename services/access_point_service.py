import network
import usocket as socket
from time import sleep
import json

__ap = None
__dns = None
__web_server = None
__running = False
__config_guardada = False
__esperando_archivos = False
__tiempo_espera = 0

def config_guardada():
    return __config_guardada

def __iniciar_web_server():
    global __web_server
    __web_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    __web_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    __web_server.bind(("0.0.0.0", 80))
    __web_server.listen(1)
    __web_server.settimeout(0)

def __procesar_dns():
    global __running, __dns
    if not __running or __dns is None:
        return
    try:
        data, addr = __dns.recvfrom(512)
        i = 12
        while True:
            length = data[i]
            if length == 0:
                break
            i += 1
            i += length

        ip_ap = "192.168.4.1"
        tid = data[:2]
        response = (
            tid +
            b"\x81\x80" +
            b"\x00\x01" +
            b"\x00\x01" +
            b"\x00\x00" +
            b"\x00\x00" +
            data[12:] +
            b"\xc0\x0c" +
            b"\x00\x01" +
            b"\x00\x01" +
            b"\x00\x00\x00\x3c" +
            b"\x00\x04" +
            bytes(map(int, ip_ap.split(".")))
        )
        __dns.sendto(response, addr)
    except:
        pass

def __iniciar_dns():
    global __dns, __running
    __running = True
    __dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    __dns.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    __dns.bind(("0.0.0.0", 53))
    __dns.settimeout(0)

def __obtener_parametro(url, nombre):
    try:
        query = url.split("?")[1]
        for p in query.split("&"):
            k, v = p.split("=")
            if k == nombre:
                return v.replace("+", " ")
    except:
        pass
    return ""

def __cargar_config():
    try:
        with open("resources/config.json", "r") as f:
            return json.load(f)
    except:
        return {"ssid": "", "password": ""}

def __guardar_config(ssid, password):
    config = {"ssid": ssid, "password": password}
    try:
        with open("resources/config.json", "w") as f:
            json.dump(config, f)
    except Exception as e:
        print("Error guardando config:", e)

def __redirigir_a_config(client):
    __enviar_respuesta(client, b"HTTP/1.1 302 Found\r\nLocation: http://configuracion.conf/\r\n\r\n")

def __leer_request(client):
    client.settimeout(2)
    data = b""
    try:
        while True:
            chunk = client.recv(256)
            if not chunk:
                break
            data += chunk
            if b"\r\n\r\n" in data:
                break
    except:
        pass
    return data.decode("utf-8", "ignore")

def __enviar_respuesta(client, data):
    if isinstance(data, str):
        data = data.encode()
    try:
        view = memoryview(data)
        total = 0
        while total < len(data):
            sent = client.send(view[total:])
            if sent == 0:
                break
            total += sent
    except:
        pass

def iniciar_ap(hostname: str):
    global __ap
    __ap = network.WLAN(network.AP_IF)
    __ap.active(True)
    __ap.config(essid=f"{hostname}", password="CONFIGURACION")
    while not __ap.active():
        sleep(1)
    __iniciar_dns()
    __iniciar_web_server()

def recibir_cliente():
    global __config_guardada, __esperando_archivos, __tiempo_espera

    for _ in range(10):
        __procesar_dns()

    if __web_server is None:
        return

    try:
        client, addr = __web_server.accept()
    except:
        if __esperando_archivos:
            __tiempo_espera += 1
            if __tiempo_espera > 50:
                __config_guardada = True
                __esperando_archivos = False
        return

    try:
        request = __leer_request(client)
        if not request:
            return
        url = request.split(" ")[1]

        if url.startswith("/guardar"):
            ssid = __obtener_parametro(url, "ssid")
            password = __obtener_parametro(url, "password")
            __guardar_config(ssid, password)

            try:
                with open("resources/pages/despedida/despedida.html", "r") as f:
                    html = f.read()
            except:
                html = "<h1>Configuracion Guardada</h1>"

            config = __cargar_config()
            html = html.replace("{{SSID}}", config["ssid"])
            __enviar_respuesta(client, "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html)

            __esperando_archivos = True
            __tiempo_espera = 0

        elif url == "/despedida":
            try:
                with open("resources/pages/despedida/despedida.html", "r") as f:
                    html = f.read()
            except:
                html = "<h1>Despedida</h1>"

            config = __cargar_config()
            html = html.replace("{{SSID}}", config["ssid"])
            __enviar_respuesta(client, "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html)

        elif url == "/configuracion.css":
            try:
                with open("resources/pages/configuracion/configuracion.css", "r") as f:
                    css = f.read()
                __enviar_respuesta(client, "HTTP/1.1 200 OK\r\nContent-Type: text/css\r\n\r\n" + css)
            except:
                __enviar_respuesta(client, b"HTTP/1.1 404 Not Found\r\n\r\n404")

        elif url == "/configuracion.js":
            try:
                with open("resources/pages/configuracion/configuracion.js", "r") as f:
                    js = f.read()
                __enviar_respuesta(client, "HTTP/1.1 200 OK\r\nContent-Type: application/javascript\r\n\r\n" + js)
            except:
                __enviar_respuesta(client, b"HTTP/1.1 404 Not Found\r\n\r\n404")

        elif url == "/despedida.css":
            try:
                with open("resources/pages/despedida/despedida.css", "r") as f:
                    css = f.read()
                __enviar_respuesta(client, "HTTP/1.1 200 OK\r\nContent-Type: text/css\r\n\r\n" + css)
            except:
                __enviar_respuesta(client, b"HTTP/1.1 404 Not Found\r\n\r\n404")

            if __esperando_archivos:
                __config_guardada = True
                __esperando_archivos = False

        elif url == "/despedida.js":
            try:
                with open("resources/pages/despedida/despedida.js", "r") as f:
                    js = f.read()
                __enviar_respuesta(client, "HTTP/1.1 200 OK\r\nContent-Type: application/javascript\r\n\r\n" + js)
            except:
                __enviar_respuesta(client, b"HTTP/1.1 404 Not Found\r\n\r\n404")

            if __esperando_archivos:
                __config_guardada = True
                __esperando_archivos = False

        elif url == "/" or url == "/configuracion.html":
            try:
                with open("resources/pages/configuracion/configuracion.html", "r") as f:
                    html = f.read()
            except:
                html = "<h1>Configuracion WiFi</h1>"

            config = __cargar_config()
            html = html.replace("{{SSID}}", config["ssid"])
            html = html.replace("{{PASSWORD}}", config["password"])
            __enviar_respuesta(client, "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html)

        else:
            __redirigir_a_config(client)

    except Exception:
        pass
    finally:
        try:
            client.close()
        except:
            pass

def cerrar_ap():
    global __ap, __dns, __web_server, __running
    __running = False

    if __dns:
        try:
            __dns.close()
        except:
            pass
        __dns = None

    if __web_server:
        try:
            __web_server.close()
        except:
            pass
        __web_server = None

    if __ap:
        try:
            __ap.active(False)
        except:
            pass
        __ap = None