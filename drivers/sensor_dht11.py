from dht import DHT11
from machine import Pin
class SensorDHT11:
    __dht : DHT11
    def __init__(self, pin : int):
        self.__dht = DHT11(Pin(pin))
    def datos(self):
        """Regresa un diccionario con indices temperatura y humedad"""
        try:
            self.__dht.measure()
            return {"temperatura": str(self.__dht.temperature()), "humedad": str(self.__dht.humidity())}
        except:
            return None