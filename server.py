import asyncio
import socket
import pickle


class ServerProtocol(asyncio.DatagramProtocol):
    __slots__ = "last_ack", "transport", "is_packet_loss", "num_packets_rcvd_after_pktloss"

    def __init__(self):
        self.transport = None
        self.last_ack = 0
        self.is_packet_loss = False
        self.num_packets_rcvd_after_pktloss = 0

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):

        tcp_packet = pickle.loads(data)
        header = tcp_packet.get_header()
        current_seq_num = header.get_seq_num()

        print(f'Received seq: {current_seq_num}')

        if current_seq_num == self.last_ack:
            if self.is_packet_loss is False:
                next_ack = current_seq_num + 1
            else:
                next_ack = self.last_ack + self.num_packets_rcvd_after_pktloss + 1
                self.is_packet_loss = False
                self.num_packets_rcvd_after_pktloss = 0
        else:
            self.is_packet_loss = True
            self.num_packets_rcvd_after_pktloss += 1
            next_ack = self.last_ack

        header.set_ack_num(next_ack)
        self.last_ack = next_ack
        self.transport.sendto(pickle.dumps(tcp_packet), addr)


async def main():
    loop = asyncio.get_running_loop()

    transport, protocol = await loop.create_datagram_endpoint(lambda: ServerProtocol(),
                                                              local_addr=(
                                                                  socket.gethostbyname(socket.gethostname()), 12349))

    try:
        print('Server started')
        await asyncio.sleep(100000)
    finally:
        transport.close()


if __name__ == '__main__':
    asyncio.run(main())
