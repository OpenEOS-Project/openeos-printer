import asyncio
import websockets
import json

client_details = {
    "id": "aaaaabsdkfjlsdkjflskdjfsldkjf"
}

PRINT_COMMAND_PING = "ping"
PRINT_COMMAND_STATUS = "status"
PRINT_COMMAND_PRINT = "print"

async def websocket_listen():
    uri = "wss://ui.openeos.de/ws/printer"

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("Connected with OpenEOS-PrintServer!")

                await websocket.send(json.dumps({
                    "command": "connect",
                    "data": client_details
                }))

                while True:
                    message = await websocket.recv()

                    try:
                        message = json.loads(message)
                        if "command" not in message:
                            print("Unknown message received!")
                            continue

                        if message["command"] == PRINT_COMMAND_PING:
                            await websocket.send(json.dumps({
                                "command": "pong"
                            }))
                        elif message["command"] == PRINT_COMMAND_STATUS and "command_id" in message:
                            await asyncio.sleep(5)
                            await websocket.send(json.dumps({
                                "command": "result",
                                "command_id": message["command_id"],
                                "data": {
                                    "status": True,
                                    "message": "Hello World"
                                }
                            }))
                        elif message["command"] == PRINT_COMMAND_PRINT and "command_id" in message:
                            if "data" in message and len(message["data"]) > 0:
                                if print(message["data"]):
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
                            print("Unknown command received!")
                            print(message)
                            continue

                    except ValueError:
                        print("Unknown message received!")
                        continue

        except (websockets.ConnectionClosed, OSError) as e:
            print("Connection closed! Try to reconnect...")
            print(e)
            await asyncio.sleep(10)

asyncio.run(websocket_listen())


def print(message: str) -> bool:
    print(message)
    return True