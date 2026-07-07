import ipaddress
import socket

from PyQt5 import QtCore as qtc

try:
    from scapy.all import ARP, Ether, srp
except Exception:
    ARP = None
    Ether = None
    srp = None


def get_local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # This does not need to succeed; it forces the OS to choose a route.
        sock.connect(("8.8.8.8", 80))
        ip_address = sock.getsockname()[0]
    except Exception:
        ip_address = "127.0.0.1"
    finally:
        sock.close()

    return ip_address


def get_subnet():
    ip_address = get_local_ip()
    network = ipaddress.ip_network(ip_address + "/24", strict=False)
    return str(network)


class NetworkScanner(qtc.QThread):
    deviceFound = qtc.pyqtSignal(dict)
    progress = qtc.pyqtSignal(int)
    finished = qtc.pyqtSignal()

    def __init__(self, subnet=None, timeout=2.0, parent=None):
        super().__init__(parent)
        self.timeout = timeout
        self._running = True
        self.subnet = subnet or self.get_subnet()

    def stop(self):
        self._running = False

    def run(self):
        try:
            print(f"[NETWORK] Scanning subnet: {self.subnet}")

            if ARP is None or Ether is None or srp is None:
                print("[NETWORK] Scapy is unavailable; skipping ARP scan")
                return

            arp = ARP(pdst=self.subnet)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether / arp

            answered, _ = srp(
                packet,
                timeout=5,
                retry=2,
                verbose=False,
            )

            total = max(len(answered), 1)
            print("===== ARP Responses =====")

            for _, received in answered:
                print(received.psrc, received.hwsrc)

            for index, (_, received) in enumerate(answered):
                if not self._running:
                    break

                device = {
                    "ip": received.psrc,
                    "mac": received.hwsrc,
                }

                print("[FOUND]", device)
                self.deviceFound.emit(device)
                self.progress.emit(int((index + 1) / total * 100))

        except Exception as error:
            print("[NETWORK ERROR]", error)

        finally:
            self._running = True
            self.finished.emit()

    def get_subnet(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            ip_address = sock.getsockname()[0]
            sock.close()

            network = ipaddress.ip_network(ip_address + "/24", strict=False)
            return str(network)

        except Exception:
            return "192.168.2.0/24"