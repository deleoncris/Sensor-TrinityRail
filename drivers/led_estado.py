from machine import Pin
class LedEstado:
    __pin_rojo : Pin
    __pin_verde : Pin
    __is_catado_comun : bool  # Anodo(-)   Catodo(+)
    def __init__(self, is_catodo_comun : bool, pin_rojo : int, pin_verde : int):
        self.__pin_rojo = Pin(pin_rojo, Pin.OUT)
        self.__pin_verde = Pin(pin_verde, Pin.OUT)
        self.__is_catado_comun = is_catodo_comun
    def mostrar_exito(self):
        if self.__is_catado_comun:
            self.__pin_rojo.off()
            self.__pin_verde.on()
        else:
            self.__pin_rojo.on()
            self.__pin_verde.off()
    def mostrar_idle(self):
        if self.__is_catado_comun:
            self.__pin_rojo.on()
            self.__pin_verde.on()
        else:
            self.__pin_rojo.off()
            self.__pin_verde.off()
    def mostrar_error(self):
        if self.__is_catado_comun:
            self.__pin_rojo.on()
            self.__pin_verde.off()
        else:
            self.__pin_rojo.off()
            self.__pin_verde.on()