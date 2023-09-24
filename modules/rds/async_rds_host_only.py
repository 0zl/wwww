import asyncio, aioredis, aiohttp, json, time, random
from aioredis.client import PubSub
from modules.shared_cmd_options import cmd_opts
from modules import shared


async def serialize(identifier, data, requestId=None, callbackId=None):
    timestamp = int(round(time.time() * 1000))
    return json.dumps({
        'ts': timestamp,
        'from': identifier,
        'data': data,
        'requestId': requestId,
        'callbackId': callbackId
    })


class RDSClient:
    client: aioredis.Redis = None
    pcl: PubSub = None
    
    def __init__(self):
        self.host = cmd_opts.rds_h
        self.port = cmd_opts.rds_p
        self.secret = cmd_opts.rds_secret
        self.identifier = cmd_opts.rds_id
        self.mother = cmd_opts.rds_mother
        self.global_chan = cmd_opts.rds_global
        self.ts_started = int(round(time.time() * 1000))
    
    async def process_message(self, msg: PubSub):
        if msg['type'] not in ['subscribe', 'message']:
            return
        
        if not isinstance(msg['data'], str):
            print(msg)
            return
        
        print(msg)
    
    async def launch_async(self):
        self.client = aioredis.Redis(
            host=self.host,
            port=self.port,
            password=self.secret,
            decode_responses=True
        )
        
        self.pcl = self.client.pubsub()
        await self.pcl.subscribe(self.global_chan)
        await self.pcl.subscribe(self.identifier)
        
        async for msg in self.pcl.listen():
            asyncio.create_task(self.process_message(msg))
    
    def launch_thread(self):
        print('evt loop thread - w4 - rd')
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.launch_async())
        # loop.close() idk?