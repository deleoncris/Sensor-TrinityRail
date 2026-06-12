class DatosDTO:
    Token : str
    Co2 : int
    Humedad: int
    Temperatura: int
    def __init__(self, token, co2, humedad, temperatura):
        self.Token = token
        self.Co2 = co2
        self.Humedad = humedad
        self.Temperatura = temperatura