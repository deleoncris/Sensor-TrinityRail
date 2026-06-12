import network
import usocket as socket
from time import sleep
import json

__ap: network.WLAN
__dns: socket.socket
__web_server: socket.socket
__running: bool = False
__config_guardada: bool = False
def config_guardada():
    return __config_guardada
def iniciar_ap(hostname: str):
    global __ap
    __ap = network.WLAN(network.AP_IF)
    __ap.active(True)
    __ap.config(essid=f"SENSOR-TR-{hostname}", password="CONFIGURACION")
    while not __ap.active():
        sleep(1)
    __iniciar_dns()
    __iniciar_web_server()
def recibir_cliente():
    try:
        client, addr = __web_server.accept()
        try:
            request = client.recv(1024).decode()
            url = request.split(" ")[1]

            if url.startswith("/guardar"):
                ssid = __obtener_parametro(url, "ssid")
                password = __obtener_parametro(url, "password")
                __guardar_config(ssid, password)

                with open("despedida.html", "r") as f:
                    html = f.read()

                config = __cargar_config()
                html = html.replace("{{SSID}}", config["ssid"])

                client.send(("HTTP/1.1 200 OK\r\n\r\n" + html).encode())
                sleep(0.4)
            else:
                with open("configuracion.html", "r") as f:
                    html = f.read()

                config = __cargar_config()
                html = html.replace("{{SSID}}", config["ssid"])
                html = html.replace("{{PASSWORD}}", config["password"])
                client.send(("HTTP/1.1 200 OK\r\n\r\n" + html).encode())
        except Exception as e:
            print("Error web config:", e)
        finally:
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
def __iniciar_web_server():
    global __web_server
    __web_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    __web_server.bind(("0.0.0.0", 80))
    __web_server.listen(5)
    __web_server.settimeout(1)
def __iniciar_dns():
    global __dns, __running
    __running = True
    __dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    __dns.bind(("0.0.0.0", 53))
    __dns.settimeout(1)
    ip_ap = "192.168.4.1"
    while __running:
        try:
            data, addr = __dns.recvfrom(512)
            qname = b""
            i = 12
            length = data[i]
            while length != 0:
                i += 1
                qname += data[i:i + length] + b"."
                i += length
                length = data[i]
            domain = qname[:-1]
            if domain != b"configuracion.conf":
                continue
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
def __guardar_config(ssid, password):
    global __config_guardada
    config = {"ssid": ssid, "password": password}
    with open("config.json", "w") as f:
        json.dump(config, f)
    __config_guardada = True
def __cargar_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except:
        return {"ssid": "", "password": ""}
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