import docker
from scapy.all import (
    Packet, Raw, IP, UDP, PcapNgWriter,
    PipeEngine, SniffSource, Sink, Drain, QueueSink
)
from typing import Optional, Dict, Any, List
import sys
sys.path.append('..')
from sippkt import SIP, RequestMessage, ResponseMessage
from sippy.SipRequest import SipRequest
from sippy.SipResponse import SipResponse
from pathlib import Path
import logging, time

app_name = Path(__file__).stem
logging.basicConfig(format="[%(asctime)s][%(levelname)s][%(name)s]: %(message)s", level=logging.INFO)
logger = logging.getLogger(app_name)

class WrpcapngSink(Sink):
    """
    An implementation similar to `WrpcapSink` to write pcapng file instead
    """
    def __init__(self, fname: str, name: Optional[str] = None) -> None:
        Sink.__init__(self, name=name)
        self.fname = fname
        self.f = None

    def start(self) -> None:
        self.f = PcapNgWriter(self.fname)

    def stop(self) -> None:
        if self.f:
            self.f.flush()
            self.f.close()

    def push(self, msg) -> None:
        if msg and self.f:
            self.f.write(msg)

def check_header(headers, key, con):
    con_met = False
    for header in headers:
        match key:
            case "cseq":
                header.body.parse()
                if header.name == key and header.body.getCSeq() == con.getCSeq():
                    con_met = True
            case "expires":
                header.body.parse()
                if header.name == key and header.body.getNum() == con.getNum():
                    con_met = True
        if con_met:
            break
    if not con_met:
        return False
    return True

def filter_sip_status_code(pkt: Packet, check=None) -> bool:
    """
    callback for `stop_filter` argument of `scapy.sniff()`
    return True to stop further sniffing if certain SIP condition is found
    #### Examples to Access Attributes of SIP Packet:
    - `pkt[SIP].summary()` return one line of str text summary.
    - `pkt[RequestMessage].Method` bytes field, e.g. `b"REGISTER"`.
    - `pkt[RequestMessage].Request_Uri` bytes field, e.g. `b"sip:sipssert-test.tw"`.
    - `pkt[ResponseMessage].Status_Code` bytes field, e.g. `b"200"`.
    - `pkt[ResponseMessage].Reason_Phrase` bytes field, e.g. `b"OK"`.
    """
    ret = True
    if SIP in pkt:
        if RequestMessage in pkt:
            reqmsg = SipRequest(pkt[SIP].original.decode())
            headers = reqmsg.headers
            if check["step"] and check["step"] == reqmsg.getMethod():
                if "expects" in check:
                    for key, con in check["expects"].items():
                        ret = check_header(headers, key, con)
                        if not ret:
                            break
            else:
                ret = False
            logger.info(f"{pkt[IP].src}:{pkt[UDP].sport} -> {pkt[IP].dst}:{pkt[UDP].dport} "
                        f"(req) {reqmsg.getMethod()} {reqmsg.getRURI()}")
        elif ResponseMessage in pkt:
            resmsg = SipResponse(pkt[SIP].original.decode())
            headers = resmsg.headers
            if check["step"] and check["step"] == resmsg.getSCode()[0]:
                if "expects" in check:
                    for key, con in check["expects"].items():
                        ret = check_header(headers, key, con)
                        if not ret:
                            break
            else:
                ret = False
            logger.info(f"{pkt[IP].src}:{pkt[UDP].sport} -> {pkt[IP].dst}:{pkt[UDP].dport} "
                        f"(res) {resmsg.getSCode()}")
        else:
            # most likely the non-SIP keep-alive packets.
            ret = False
            logger.info(f"{pkt[IP].src}:{pkt[UDP].sport} -> {pkt[IP].dst}:{pkt[UDP].dport} "
                        f"(raw) {pkt[Raw].load}")
    else:
        # not likely to see this if BPF filter is set properly in sniff()
        ret = False
        logger.info(f"{pkt[IP].src}:{pkt[UDP].sport} -> {pkt[IP].dst}:{pkt[UDP].dport}\n\t{pkt[Raw].load}")
    return ret

class PipeManager:
    """
    A class for manage sniffing pipe
    """
    def __init__(self, infc: str) -> None:
        # constructing source, drain, and sinks
        self.src_sniff = SniffSource(iface=infc, filter="udp and ((host 172.21.23.1 or 172.21.23.254) and (host 172.21.23.30 or host 172.21.23.31 or host 172.21.23.32))")
        self.drain = Drain()
        pcap_filename = f"{app_name}-{time.strftime('%y%m%d-%H%M%S', time.localtime())}.pcapng"
        self.snk_wpcap = WrpcapngSink(fname=pcap_filename)
        self.snk_queue = QueueSink()
        
        # link source, drain, and sinks to build a processing pipeline
        self.src_sniff > self.drain
        self.drain > self.snk_wpcap
        self.drain > self.snk_queue

        self.pipe = PipeEngine(self.src_sniff)

    def pipe_start(self) -> None:
        logger.info("start sniffing pipeline.")
        self.pipe.start()

    def pipe_stop(self, code: list, timeout: float) -> None:
        """
        Stop the pipeline when packet conditions are met sequentially.
        Parameters:
        - code (list): A list of conditions to check sequentially, should be like [[req1, res1], [req2, res2]].
        """
        # blocking receive from queue sink with `select` timeout
        time_start = time.monotonic()
        for condition in code:
            if "times" in condition:
                count = condition["times"]
            else:
                count = 1
            while True:
                if timeout <= (time.monotonic() - time_start):
                    logger.info("Timeout reached. Condition not met within the specified timeout.")
                    break
                pkt = self.snk_queue.recv(block=False, timeout=0.3)
                # check if the conditions is satisfied
                if pkt is not None and filter_sip_status_code(pkt, condition):
                    count = count-1
                    if count <= 0:
                        logger.info(f"met the condition {condition}")
                        break
        logger.info("stop sniffing pipeline.")
        self.pipe.stop()

class DockerClient:
    def __init__(self) -> None:
        self.client = docker.from_env()
        self.container = dict()
        self.network = None
    
    def disconnect(self, container: str, interface: str = "test-network") -> None:
        self.network = self.client.networks.get(interface) if not self.network else self.network
        self.network.disconnect(container)
        logger.info(f"disconnect {container} from {interface}")
    
    def connect(self, container: str, ipv4_address: str, interface: str = "test-network") -> None:
        self.network = self.client.networks.get(interface) if not self.network else self.network
        self.network.connect(container, ipv4_address)
        logger.info(f"connect {container} to {interface} with ip {ipv4_address}")
    
    def get_container(self, container_name: str) -> None:
        if container_name not in self.container:
            self.container[container_name] = self.client.containers.get(container_name)
            logger.info(f"get {container_name}")
    
    def list_containers(self) -> None:
        cont_list = [c.name for c in self.client.containers.list()]
        logger.info(f"container list {cont_list}")

    def wait(self, name: str) -> None:
        self.get_container(name)
        logger.info(f"waiting for {name}...")
        self.container[name].wait()
        logger.info(f"{name} has exited")

    def exec_in_container(self, container_name: str, command: str, infc: str = None, conditions: list = [], timeout: float = 60.0) -> None:
        container_name = container_name.strip()
        self.get_container(container_name)
        pipe_manager = PipeManager(infc) if infc else None
        pipe_manager.pipe_start() if infc else None
        result = self.container[container_name].exec_run(command)
        logger.info(f"run command '{command}' in {container_name}")
        logger.info(result.output.decode("utf-8"))
        pipe_manager.pipe_stop(conditions, timeout) if infc else None

    def wait_packet(self, infc: str = None, conditions: list = [], timeout: float = 60.0) -> None:
        pipe_manager = PipeManager(infc)
        pipe_manager.pipe_start()
        pipe_manager.pipe_stop(conditions, timeout)