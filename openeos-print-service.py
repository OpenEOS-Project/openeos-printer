#!.venv/bin/python

import asyncio
import websockets
import json
import logging

import websockets.exceptions

from escpos.printer import Usb
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename="/var/log/openeos/print-service.log")

def log(message: str):
    print(datetime.now().strftime("%Y-%m-%d %H:%M") + " " + message)
    logging.info(message)

try:
    client_details = json.load(open(".config.json", "r"))
except:
    log("No configuration file found!")
    exit(1)

PRINT_COMMAND_PING = "ping"
PRINT_COMMAND_STATUS = "status"
PRINT_COMMAND_PRINT = "print"

COLCOUNT = 48

#printer = Usb(0x04b8, 0x0202, 0, profile="TM-T20II")
printer = Usb(0x04b8, 0x0e15, 0, profile="TM-T20II")

def print_on_printer(message: list[str]) -> bool:
    """
    
    # Hallo Welt -> double height

    _ Hallo Welt -> centered with whitespace

    _# Hallo Welt -> double height and centered

    _#= Hallo Welt -> double height, centered and filled with =
    
    """
    for line in message:
        if line.startswith("#"):
            printer.set(double_height=True)
        elif line.startswith("!"):
            line = (" " + line + " ").center(COLCOUNT, "=")
            printer.set(double_height=True)
        elif line.startswith("_#"):
            line = (" " + line + " ").center(COLCOUNT, " ")
            printer.set(double_height=True)
        elif line.startswith("_"):
            line = (" " + line + " ").center(COLCOUNT, " ")

        printer.textln(line.replace("#", "").replace("_", "").replace("!", ""))

        # reset all printer settings
        printer.set(normal_textsize=True)

    printer.cut()

    return True

def get_printer_paper_status() -> str:
    paper_status = printer.paper_status()
    status = "n/a"
    if paper_status == 2:
        status = "PAPER_GOOD"
    elif paper_status == 1:
        status = "PAPER_ENDING"
    elif paper_status == 0:
        status = "NO_PAPER"

    log(f"-> Read paper status from printer: {status}")
    return status

async def websocket_listen():
    uri = "wss://ui.openeos.de/ws/printer"

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                log("Connected with OpenEOS-PrintServer!")

                client_details["paper"] = get_printer_paper_status()

                await websocket.send(json.dumps({
                    "command": "connect",
                    "data": client_details
                }))

                while True:
                    message = await websocket.recv()

                    try:
                        message = json.loads(message)
                        if "command" not in message:
                            log("Unknown message received!")
                            continue

                        if message["command"] == PRINT_COMMAND_PING:
                            await websocket.send(json.dumps({
                                "command": "pong"
                            }))
                        elif message["command"] == PRINT_COMMAND_STATUS and "command_id" in message:
                            await websocket.send(json.dumps({
                                "command": "result",
                                "command_id": message["command_id"],
                                "data": {
                                    "status": True,
                                    "message": get_printer_paper_status()
                                }
                            }))
                        elif message["command"] == PRINT_COMMAND_PRINT and "command_id" in message:
                            if "data" in message and len(message["data"]) > 0:
                                if print_on_printer(message["data"]):
                                    await websocket.send(json.dumps({
                                        "command": "result",
                                        "command_id": message["command_id"],
                                        "data": {
                                            "status": True,
                                            "message": "Printed successfully!"
                                        }
                                    }))
                                else:
                                    await websocket.send(json.dumps({
                                        "command": "result",
                                        "command_id": message["command_id"],
                                        "data": {
                                            "status": False,
                                            "message": "Failed to print!"
                                        }
                                    }))
                        else:
                            log("Unknown command received!")
                            log(message)
                            continue

                    except ValueError:
                        log("Unknown message received!")
                        continue

        except (websockets.ConnectionClosed, OSError, websockets.exceptions.InvalidStatus) as e:
            log(f"############################################")
            log(f"# --> Connection closed! Try to reconnect...")
            log(f"# --> {e}")
            log(f"############################################")
            await asyncio.sleep(10)

try:
    asyncio.run(websocket_listen())
except KeyboardInterrupt:
    exit(0)