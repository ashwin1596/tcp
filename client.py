import asyncio
import socket
import pickle
import random
from asyncio import BaseTransport

from model.congestion_wnd import CongestionWindow
from model.tcp_header import TCPHeader
from model.tcp_packet import TCPPacket


class ClientProtocol(asyncio.DatagramProtocol):
    __slots__ = "response_list"

    def __init__(self):
        self.response_list = asyncio.Queue()

    def datagram_received(self, data, addr):
        self.response_list.put_nowait(data)

    def error_received(self, exc):
        print(f'Received an error: {exc}')

    def connection_lost(self, exc):
        if exc is None:
            print("Connection closed successfully")
        else:
            print(f'Lost the connection due to an error: {exc}')

    async def receive_from(self):
        return await self.response_list.get()


def get_serialized_packet(seq_num):
    data = "Hello World"

    tcp_header = TCPHeader()
    tcp_header.set_seq_num(seq_num)

    tcp_packet = TCPPacket()
    tcp_packet.set_header(tcp_header)
    tcp_packet.set_data(data)

    return pickle.dumps(tcp_packet)


def fast_retransmission(packet: bytes, retransmission_pkt_seq, transport: BaseTransport,
                        congestion_wnd: CongestionWindow):
    transport.sendto(packet)  # retransmit
    print(f'Retransmitted packet: {retransmission_pkt_seq}')
    new_ssthresh = congestion_wnd.get_cwnd() // 2
    congestion_wnd.reset_cwnd()
    return new_ssthresh


async def main():
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: ClientProtocol(),
        remote_addr=(socket.gethostbyname(socket.gethostname()), 12349))

    congestion_wnd = CongestionWindow()

    try:
        print('Client Started')

        num_rtt = 20  # testing purpose
        rtt_completed = 0  # testing purpose
        time_out = 5
        ss_thresh = 8
        cwnd_offset = 0
        num_packets_sent = 0

        last_ack = 0
        dup_acks = 0

        is_packet_loss = False
        lost_packet_seq = None

        # while True:  # one RTT
        while rtt_completed < num_rtt:
            task_list = []
            received_responses = []
            while num_packets_sent < (cwnd_offset + congestion_wnd.get_cwnd()):  # sending one window

                next_seq_num = num_packets_sent

                if random.random() <= 0.01:
                    is_packet_loss = True
                    lost_packet_seq = next_seq_num
                    num_packets_sent += 1
                    continue

                data_to_send = get_serialized_packet(next_seq_num)
                transport.sendto(data_to_send)

                congestion_wnd.add_packet_in_flight(next_seq_sent=next_seq_num)
                task_list.append(protocol.receive_from())
                num_packets_sent += 1

            # print packets in flight
            print(
                f'\nCONGESTION WINDOW: (size = {congestion_wnd.get_cwnd()}) \n{congestion_wnd.get_packets_in_flight()}')

            if is_packet_loss:
                print(f'Lost packet: {lost_packet_seq}')
                lost_packet_seq = None

            completed_tasks, pending_tasks = await asyncio.wait(task_list,
                                                                timeout=time_out,
                                                                return_when=asyncio.FIRST_EXCEPTION)

            for future in completed_tasks:
                try:
                    response = await future
                    response_packet = pickle.loads(response)
                    received_ack = response_packet.get_header().get_ack_num()

                    received_responses.append(received_ack)

                except Exception as e:
                    print(f"Exception occurred: {e}")

            # handle the received responses
            received_responses.sort()

            print(f'{"".join(str(received_responses))}  <= Received Acks')

            for received_ack in received_responses:
                if len(congestion_wnd.get_packets_in_flight()) != 0:
                    # handling dup_Acks
                    if last_ack == received_ack:
                        dup_acks += 1

                        if dup_acks == 3:
                            lost_packet_seq = last_ack
                            ss_thresh = fast_retransmission(get_serialized_packet(lost_packet_seq), lost_packet_seq,
                                                            transport, congestion_wnd)
                            retransmission_response = await protocol.receive_from()
                            retransmission_response_packet = pickle.loads(retransmission_response)
                            retransmission_received_ack = retransmission_response_packet.get_header().get_ack_num()
                            print(f'{retransmission_received_ack}  <= Received Ack after retransmission')
                            congestion_wnd.remove_packet_in_flight(retransmission_received_ack)
                            last_ack = retransmission_received_ack
                            continue
                    else:
                        congestion_wnd.remove_packet_in_flight(received_ack)

                    last_ack = received_ack
                else:
                    break

            # waiting for the completion of completed tasks
            remaining_tasks = [task for task in pending_tasks]
            remaining_results = await asyncio.gather(*remaining_tasks)

            cwnd_offset += congestion_wnd.get_cwnd_before_reset() if is_packet_loss else congestion_wnd.get_cwnd()

            if congestion_wnd.get_cwnd() < ss_thresh:  # slow start
                if not is_packet_loss:
                    congestion_wnd.ss_increase_cwnd()
                else:
                    is_packet_loss = False
            else:
                congestion_wnd.cavd_increase_cwnd()

            rtt_completed += 1


    finally:
        transport.close()


if __name__ == '__main__':
    asyncio.run(main())
