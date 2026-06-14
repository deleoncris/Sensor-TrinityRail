from machine import Pin, ADC
class SensorMQ5:
    __mq5 : ADC
    def __init__(self, pin : int):
        self.__mq5 = ADC(Pin(pin))
    def valor(self):
        raw = float(self.__mq5.read_u16())
        data_without_format = 0.007629511 * raw
        return str(int(data_without_format))