class TCPHeader:
    __slots__ = "ack_num", "seq_num"

    def __init__(self):
        self.ack_num = None
        self.seq_num = None

    def __str__(self):
        return f'Seq-{self.seq_num}, Ack-{self.ack_num}'

    def set_ack_num(self, ack):
        self.ack_num = int(ack)

    def get_ack_num(self):
        return self.ack_num

    def set_seq_num(self, seq):
        self.seq_num = seq

    def get_seq_num(self):
        return self.seq_num
