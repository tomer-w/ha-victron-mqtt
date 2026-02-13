#!/usr/bin/env python3
"""
Script to send SSDP discovery packet to trigger Victron MQTT integration in Home Assistant.
This simulates a Victron device announcing itself on the network.
"""

import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900
HTTP_PORT = 8080


def get_local_ip():
    """Get the local IP address that can reach the multicast group."""
    # Try to determine which IP to use by creating a socket to the multicast address
    try:
        # Create a socket and connect to a public IP to determine our local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        # Fallback to localhost
        return "127.0.0.1"


DEVICE_IP = get_local_ip()


# UPnP device description XML
DEVICE_DESCRIPTION = """<?xml version="1.0"?>
<root xmlns="urn:schemas-upnp-org:device-1-0">
  <specVersion>
    <major>1</major>
    <minor>0</minor>
  </specVersion>
  <device>
    <deviceType>urn:schemas-upnp-org:device:Basic:1</deviceType>
    <friendlyName>Venus GX Test</friendlyName>
    <manufacturer>Victron Energy</manufacturer>
    <manufacturerURL>https://www.victronenergy.com</manufacturerURL>
    <modelDescription>Victron Venus GX</modelDescription>
    <modelName>Cerbo GX</modelName>
    <modelNumber>1.0</modelNumber>
    <serialNumber>HQ2234TEST</serialNumber>
    <UDN>uuid:victron-test-12345</UDN>
    <X_VrmPortalId>1adbeb923220</X_VrmPortalId>
    <X_MqttOnLan>1</X_MqttOnLan>
  </device>
</root>
"""


class DeviceDescriptionHandler(BaseHTTPRequestHandler):
    """HTTP handler to serve device description XML."""

    def do_GET(self):
        """Handle GET requests for device description."""
        if self.path == "/description.xml":
            self.send_response(200)
            self.send_header("Content-Type", "text/xml")
            self.send_header("Content-Length", len(DEVICE_DESCRIPTION))
            self.end_headers()
            self.wfile.write(DEVICE_DESCRIPTION.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Override to customize logging."""
        print(f"[HTTP] {args[0]}")


def start_http_server():
    """Start HTTP server to serve device description."""
    server = HTTPServer((DEVICE_IP, HTTP_PORT), DeviceDescriptionHandler)
    print(f"[HTTP] Device description server started on http://{DEVICE_IP}:{HTTP_PORT}")
    print(
        f"[HTTP] Serving description at http://{DEVICE_IP}:{HTTP_PORT}/description.xml"
    )
    server.serve_forever()


def send_ssdp_notify():
    """Send SSDP NOTIFY packet for Victron device discovery."""
    location = f"http://{DEVICE_IP}:{HTTP_PORT}/description.xml"

    # SSDP NOTIFY message - this announces the device
    message = (
        "NOTIFY * HTTP/1.1\r\n"
        f"HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n"
        "CACHE-CONTROL: max-age=1800\r\n"
        f"LOCATION: {location}\r\n"
        "NT: upnp:rootdevice\r\n"
        "NTS: ssdp:alive\r\n"
        "SERVER: Linux/5.10 UPnP/1.0 Victron/1.0\r\n"
        "USN: uuid:victron-test-12345::upnp:rootdevice\r\n"
        "\r\n"
    )

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    try:
        # Send the SSDP packet
        sock.sendto(message.encode("utf-8"), (SSDP_ADDR, SSDP_PORT))
        print(f"[SSDP] NOTIFY packet sent to {SSDP_ADDR}:{SSDP_PORT}")
        print(f"[SSDP] Location: {location}")
        print("\n[SSDP] Packet content:")
        print(message)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send SSDP packet: {e}")
        return False
    finally:
        sock.close()


def send_periodic_ssdp(interval=30):
    """Send SSDP notifications periodically."""
    import time

    while True:
        send_ssdp_notify()
        print(f"[SSDP] Next announcement in {interval} seconds...")
        time.sleep(interval)


if __name__ == "__main__":
    import time

    print("=" * 70)
    print("Victron MQTT SSDP Emulator")
    print("=" * 70)
    print("\nThis script emulates a Victron device on the network by:")
    print("1. Starting an HTTP server to serve UPnP device description XML")
    print("2. Sending SSDP NOTIFY packets to announce the device")
    print("\nConfiguration:")
    print(f"  Device IP:   {DEVICE_IP}")
    print(f"  HTTP Port:   {HTTP_PORT}")
    print(f"  SSDP Addr:   {SSDP_ADDR}:{SSDP_PORT}")
    print("\nDevice Details:")
    print("  Model:       Cerbo GX")
    print("  Name:        Venus GX Test")
    print("  Serial:      HQ2234TEST")
    print("  Portal ID:   d41243d9b9c6")
    print("=" * 70)

    # Start HTTP server in background thread
    print("\n[1/3] Starting HTTP server...")
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

    # Give server time to start
    time.sleep(0.5)

    # Verify HTTP server is running
    print("[HTTP] Testing server...")
    try:
        import urllib.request

        with urllib.request.urlopen(
            f"http://{DEVICE_IP}:{HTTP_PORT}/description.xml", timeout=2
        ) as response:
            if response.status == 200:
                print("[HTTP] ✓ Server is responding correctly")
            else:
                print(f"[HTTP] ✗ Server returned status {response.status}")
    except Exception as e:
        print(f"[HTTP] ✗ Server test failed: {e}")
        print("[ERROR] HTTP server is not running properly!")
        sys.exit(1)

    # Send SSDP notification
    print("\n[2/3] Sending initial SSDP NOTIFY packet...")
    success = send_ssdp_notify()

    if success:
        print("\n[3/3] Starting periodic SSDP announcements...")
        print("\n" + "=" * 70)
        print("SUCCESS! Emulator is running.")
        print("=" * 70)
        print("\n✓ HTTP server is running and serving device description")
        print("✓ SSDP announcements will be sent every 30 seconds")
        print("\nHome Assistant should discover the device if it's listening for SSDP.")
        print("\nYou can test the description XML in another terminal:")
        print(f"  curl http://{DEVICE_IP}:{HTTP_PORT}/description.xml")
        print("\nPress Ctrl+C to stop the emulator...")
        print("=" * 70 + "\n")

        try:
            # Send periodic SSDP announcements
            send_periodic_ssdp(interval=30)
        except KeyboardInterrupt:
            print("\n\n" + "=" * 70)
            print("Shutting down...")
            print("=" * 70)
            sys.exit(0)
    else:
        print("\n[ERROR] Failed to send SSDP packet!")
        print("Make sure you have network permissions (may need sudo)")
        sys.exit(1)
