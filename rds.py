import aioredis, asyncio, json, requests, time, random
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
            print(msg)


async def launch():
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--rds-h', type=str, default='localhost')
    parser.add_argument('--rds-p', type=int, default=6379)
    parser.add_argument('--rds-secret', type=str, default='secret')
    parser.add_argument('--rds-id', type=str, default='id')
    parser.add_argument('--rds-mother', type=str, default='mother')
    parser.add_argument('--rds-global', type=str, default='global')
    
    gs = parser.parse_args()
    
    rds = RDS(gs)
    await rds.launch()

if __name__ == "__main__":
    print('- w4 -')
    asyncio.run(launch())
    
