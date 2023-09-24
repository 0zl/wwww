import aioredis, asyncio, json, time, random, aiohttp
import argparse
from aioredis.client import PubSub


def serialize(id, data, request_id=None, callback_id=None):
    ts = int(round(time.time() * 1000))
    return json.dumps({
        'ts': ts,
        'from': id,
        'data': data,
        'requestId': request_id,
        'callbackId': callback_id
    })


class RDS:
    client: aioredis.Redis = None
    pcl: PubSub = None
    
    def __init__(self, gs):
        self.host = gs.rds_h
        self.port = gs.rds_p
        self.secret = gs.rds_secret
        self.identifier = gs.rds_id
        self.mother = gs.rds_mother
        self.global_chan = gs.rds_global
        self.w4_port = gs.w4_port
        self.ts_started = int(round(time.time() * 1000))
    
    async def launch(self):
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
    
    async def handle_global_call(self, msg: PubSub):
        if msg['channel'] != self.global_chan:
            return False
        
        return True

    async def process_message(self, msg: PubSub):
        if msg['type'] not in ['subscribe', 'message']:
            return

        if not isinstance(msg['data'], str):
            print(msg)
            return

        if await self.handle_global_call(msg):
            return

async def launch(rds: RDS):
    await rds.launch()

if __name__ == "__main__":
    print('- w4 -')
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--rds-h', type=str, default='localhost', required=True)
    parser.add_argument('--rds-p', type=int, default=6379, required=True)
    parser.add_argument('--rds-secret', type=str, default='secret', required=True)
    parser.add_argument('--rds-id', type=str, default='id', required=True)
    parser.add_argument('--rds-mother', type=str, default='mother', required=True)
    parser.add_argument('--rds-global', type=str, default='global', required=True)
    parser.add_argument('--w4-port', type=int, default=8081, required=True)
    
    gs = parser.parse_args()
    
    rds = RDS(gs)
    asyncio.run(launch(rds))
    
