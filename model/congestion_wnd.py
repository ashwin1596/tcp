class CongestionWindow:
    __slots__ = "cwnd", "packets_in_flight", "cwnd_before_reset"

    def __init__(self):
        self.cwnd = 1
        self.cwnd_before_reset = 1
        self.packets_in_flight = []  # this will be used to show cwnd sliding

    def __str__(self):
        return '\n'.join(self.packets_in_flight)

    def add_packet_in_flight(self, next_seq_sent):
        self.packets_in_flight.append(next_seq_sent)

    def remove_packet_in_flight(self, ack_received):

        seq = ack_received - 1

        # self.packets_in_flight.remove(ack_received - 1)

        if seq == self.packets_in_flight[0]:
            self.packets_in_flight.remove(ack_received - 1)
        elif seq == self.packets_in_flight[len(self.packets_in_flight) - 1]:
            self.packets_in_flight = []
        # else:
        #     pass

    def cavd_increase_cwnd(self):
        self.cwnd += 1
        self.cwnd_before_reset = self.cwnd

    def ss_increase_cwnd(self):
        self.cwnd *= 2
        self.cwnd_before_reset = self.cwnd

    def reset_cwnd(self):
        self.cwnd = 1

    def get_cwnd(self):
        return self.cwnd

    def get_packets_in_flight(self):
        return self.packets_in_flight

    def get_cwnd_before_reset(self):
        response = self.cwnd_before_reset
        self.cwnd_before_reset = self.cwnd
        return response
