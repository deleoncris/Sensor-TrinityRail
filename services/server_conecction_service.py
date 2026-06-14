import socket
import asyncio
import ujson

from drivers.led_estado import LedEstado

__sock: socket = None
__ip_servidor: str = ""
__token: str = ""
__numero_serie: str = ""
__led_estado: LedEstado = None


def conectado():
    return __token != "" and __ip_servidor != ""


async def registrarse(numero_serie: str, led_servidor: LedEstado):
    global __token, __ip_servidor, __numero_serie, __led_estado

    __numero_serie = numero_serie
    if __led_estado is None:
        __led_estado = led_servidor

    __led_estado.mostrar_idle()

    if __token != "" and __ip_servidor != "":
        await __renovar_registro()
        return

    if __ip_servidor == "":
        __led_estado.mostrar_idle()
        encontrado = await __ubicar_server_con_reintentos()
        if not encontrado:
            __led_estado.mostrar_error()
            await asyncio.sleep(30)
            asyncio.create_task(registrarse(__numero_serie, __led_estado))
            return

    if __token == "":
        __led_estado.mostrar_idle()
        obtenido = await __solicitar_token_con_reintentos(numero_serie)
        if not obtenido:
            __led_estado.mostrar_error()
            await asyncio.sleep(30)
            asyncio.create_task(registrarse(__numero_serie, __led_estado))
            return

    __led_estado.mostrar_exito()
    asyncio.create_task(__renovar_registro())


def __parsear_respuesta_http(response_bytes: bytes):
    try:
        response_str = response_bytes.decode('utf-8')

        if '\r\n\r\n' in response_str:
            headers_part, body = response_str.split('\r\n\r\n', 1)
        else:
            headers_part = response_str
            body = ""

        lines = headers_part.split('\r\n')
        status_line = lines[0] if lines else ""

        status_code = 0
        if 'HTTP/' in status_line:
            parts = status_line.split(' ')
            if len(parts) >= 2:
                try:
                    status_code = int(parts[1])
                except ValueError:
                    pass

        headers = {}
        for line in lines[1:]:
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key.lower()] = value

        return status_code, body, headers
    except Exception:
        return 0, "", {}


def mandar_datos(temperatura: str, humedad: str, co2: str):
    global __token, __ip_servidor

    if not conectado():
        return

    try:
        host = __ip_servidor
        port = 5221
        path = "/Sensores/GuardarDatos"

        data = {
            "token": __token,
            "co2": co2,
            "temperatura": temperatura,
            "humedad": humedad
        }

        body = ujson.dumps(data)

        request = f"POST {path} HTTP/1.1\r\n"
        request += f"Host: {host}:{port}\r\n"
        request += "Content-Type: application/json\r\n"
        request += f"Content-Length: {len(body)}\r\n"
        request += "Connection: close\r\n"
        request += "\r\n"
        request += body

        s = socket.socket()
        s.settimeout(5)
        s.connect((host, port))
        s.send(request.encode())

        response = b""
        while True:
            try:
                data_chunk = s.recv(1024)
                if not data_chunk:
                    break
                response += data_chunk
            except:
                break

        s.close()

        status_code, body_resp, headers = __parsear_respuesta_http(response)

        if status_code == 200:
            if "Guardado" in body_resp:
                if __led_estado:
                    __led_estado.mostrar_exito()
            else:
                if __led_estado:
                    __led_estado.mostrar_error()
        elif status_code == 400:
            if __led_estado:
                __led_estado.mostrar_error()

            if "Token inexistente" in body_resp:
                __token = ""
                asyncio.create_task(registrarse(__numero_serie, __led_estado))
        else:
            if __led_estado:
                __led_estado.mostrar_error()

    except Exception:
        if __led_estado:
            __led_estado.mostrar_error()


async def __ubicar_server_con_reintentos():
    global __ip_servidor

    max_intentos = 3
    intento = 0

    while intento < max_intentos and __ip_servidor == "":
        __ubicar_server()

        if __ip_servidor == "":
            intento += 1
            if intento < max_intentos:
                await asyncio.sleep(5)

    return __ip_servidor != ""


def __ubicar_server():
    global __ip_servidor

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)
    sock.bind(("0.0.0.0", 50000))

    try:
        data, addr = sock.recvfrom(1024)
        mensaje = data.decode("utf-8")
        if mensaje == "Servidor Trinity Rail":
            __ip_servidor = str(addr[0])
    except Exception:
        pass
    finally:
        sock.close()


async def __solicitar_token_con_reintentos(numero_serie: str):
    global __token

    max_intentos = 3
    intento = 0

    while intento < max_intentos and __token == "":
        __solicitar_token(numero_serie)

        if __token == "":
            intento += 1
            if intento < max_intentos:
                await asyncio.sleep(5)

    return __token != ""


def __solicitar_token(numero_serie: str):
    global __token, __ip_servidor

    if __ip_servidor == "":
        return

    try:
        host = __ip_servidor
        port = 5221
        path = f"/Autentificacion/RegistrarDispositivo?numeroSerieDispositivo={numero_serie}"

        request = f"POST {path} HTTP/1.1\r\n"
        request += f"Host: {host}:{port}\r\n"
        request += "User-Agent: ESP32-MicroPython/1.0\r\n"
        request += "Accept: */*\r\n"
        request += "Connection: close\r\n"
        request += "\r\n"

        s = socket.socket()
        s.settimeout(10)
        s.connect((host, port))
        s.send(request.encode())

        response = b""
        while True:
            data = s.recv(1024)
            if not data:
                break
            response += data

        s.close()

        status_code, body, headers = __parsear_respuesta_http(response)

        if status_code == 200:
            token_limpio = body.strip()
            if token_limpio.startswith('"') and token_limpio.endswith('"'):
                token_limpio = token_limpio[1:-1]

            if token_limpio and len(token_limpio) > 0:
                __token = token_limpio[4:len(token_limpio) - 3]
        elif status_code == 400:
            __token = ""
        else:
            __token = ""

    except Exception:
        __token = ""


async def __renovar_registro():
    global __token, __ip_servidor

    while True:
        await asyncio.sleep(60)

        if not conectado():
            if __led_estado:
                __led_estado.mostrar_error()

            __token = ""
            __ip_servidor = ""

            await registrarse(__numero_serie, __led_estado)
            continue

        try:
            host = __ip_servidor
            port = 5221
            path = f"/Autentificacion/RenovarAutentificacion?token={__token}"

            request = f"POST {path} HTTP/1.1\r\n"
            request += f"Host: {host}:{port}\r\n"
            request += "Connection: close\r\n"
            request += "\r\n"

            s = socket.socket()
            s.settimeout(5)
            s.connect((host, port))
            s.send(request.encode())

            response = b""
            while True:
                try:
                    data = s.recv(1024)
                    if not data:
                        break
                    response += data
                except:
                    break

            s.close()

            status_code, body, headers = __parsear_respuesta_http(response)

            if status_code == 200:
                if __led_estado and conectado():
                    __led_estado.mostrar_exito()
            elif status_code == 404:
                if __led_estado:
                    __led_estado.mostrar_error()
                __token = ""
                await asyncio.sleep(5)
                await registrarse(__numero_serie, __led_estado)
            elif status_code == 400:
                if __led_estado:
                    __led_estado.mostrar_error()
                __token = ""
                await registrarse(__numero_serie, __led_estado)
            else:
                if __led_estado:
                    __led_estado.mostrar_error()

        except Exception:
            if __led_estado:
                __led_estado.mostrar_error()
            __ip_servidor = ""
            await asyncio.sleep(10)