# -*- coding: utf-8 -*-
import requests
from urllib.parse import urljoin

import json

from aiohttp import ClientSession
import asyncio
import websockets
import aiofiles

import os

from faraday_agent_dispatcher.executor_helper import FIFOLineProcessor, StdErrLineProcessor, StdOutLineProcessor
import faraday_agent_dispatcher.logger as logging

logger = logging.get_logger()

LOG = False


class Dispatcher:

    def __init__(self, url, workspace, agent_token, executor_filename, api_port="5985", websocket_port="9000"):
        self.__url = url
        self.__api_port = api_port
        self.__websocket_port = websocket_port
        self.__workspace = workspace
        self.__agent_token = agent_token
        self.__executor_filename = executor_filename
        self.__session = ClientSession()
        self.__websocket = None
        self.__websocket_token = None
        self.__command = None

    def __get_url(self, port):
        return f"{self.__url}:{port}"

    def __api_url(self, secure=False):
        prefix = "https://" if secure else "http://"
        return f"{prefix}{self.__get_url(self.__api_port)}"

    def __websocket_url(self, secure=False):
        prefix = "wss://" if secure else "ws://"
        return f"{prefix}{self.__get_url(self.__websocket_port)}"

    async def reset_websocket_token(self):
        # I'm built so I ask for websocket token
        headers = {"Authorization": f"Agent {self.__agent_token}"}
        d = f'{self.__api_url()}/_api/v2/agent_websocket_token/'
        websocket_token_response = await self.__session.post(
            f'{self.__api_url()}/_api/v2/agent_websocket_token/',
            headers=headers)

        websocket_token_json = await websocket_token_response.json()  # TODO ERRORS
        self.__websocket_token = websocket_token_json["token"]

    async def connect(self):
        # I'm built so I can connect
        if self.__websocket_token is None:
            await self.reset_websocket_token()

        async with websockets.connect(self.__websocket_url()) as websocket:
            await websocket.send(json.dumps({
                'action': 'JOIN_AGENT',
                'workspace': self.__workspace,
                'token': self.__websocket_token,
            }))

            self.__websocket = websocket

            await self.run_await()  # This line can we called from outside (in main)

    async def disconnect(self):
        await self.__session.close()
        await self.__websocket.close()

    # V2
    async def run_await(self):
        # Next line must be uncommented, when faraday (and dispatcher) maintains the keep alive
        data = await self.__websocket.recv()
        # TODO Control data
        fifo_name = Dispatcher.rnd_fifo_name()
        Dispatcher.create_fifo(fifo_name)
        process = await self.create_process(fifo_name)
        async with aiofiles.open(fifo_name, "r") as fifo_file:
            tasks = [StdOutLineProcessor(process).process_f(),
                     StdErrLineProcessor(process).process_f(),
                     FIFOLineProcessor(fifo_file).process_f(),
                     self.run_await()]

            await asyncio.gather(*tasks)
            await process.communicate()

    @staticmethod
    def create_fifo(fifo_name):
        if os.path.exists(fifo_name):
            os.remove(fifo_name)
        os.mkfifo(fifo_name)

    @staticmethod
    def rnd_fifo_name():
        import string
        from random import choice
        chars = string.ascii_letters + string.digits
        name = "".join(choice(chars) for _ in range(10))
        return f"/tmp/{name}"

    async def create_process(self, fifo_name):
        new_env = os.environ.copy()
        new_env["FIFO_NAME"] = fifo_name
        process = await asyncio.create_subprocess_shell(
            self.__executor_filename, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=new_env
        )
        return process

    async def send(self):
        # Any time can be called by IPC

        # Send by API and Agent Token the info
        url = urljoin(self.__url, "_api/v2/ws/"+ self.__workspace +"/hosts/")

        aa = requests.get(url, headers={"token": self.__token})
        aaa = requests.get(url, headers={"token": self.a})
        pass

