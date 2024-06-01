class TCPPacket:
    __slots__ = "header", "data"

    def __init__(self):
        self.header = None
        self.data = None

    def __str__(self):
        return f'Header: {self.header}, Data: {self.data}'

    def set_header(self, header):
        self.header = header

    def get_header(self):
        return self.header

    def set_data(self, data):
        self.data = data

    def get_data(self):
        return self.data
