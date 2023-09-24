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
    
    async def send_data(self, data, success=True, request_id=None, channel=None):
        if hasattr(data, '__dict__'):
            data = data.__dict__
        elif type(data) is list:
            list_data = []
            for i, e in enumerate(data):
                list_data.append(e)
            data = { 'list': list_data }
        elif isinstance(data, str):
            data = { 'info': data }

        n_data = { 'success': success, **data }
        serialized_data = await serialize(self.identifier, n_data, callbackId=request_id)
        
        await self.client.publish(
            self.mother if channel is None else channel,
            serialized_data
        )
        
    async def ping_status(self, channel=None):
        print('w4 - gc ping')
        
        url = f'http://127.0.0.1:{cmd_opts.port}'
        async with aiohttp.ClientSession() as session:
            try:
                async with session.head(url) as resp:
                    if resp.status == 200:
                        status = 'online'
                    else:
                        if shared.is_model_ready:
                            status = 'offline'
                        else:
                            status = 'booting'
            except aiohttp.ClientConnectionError:
                if shared.is_model_ready:
                    status = 'offline'
                else:
                    status = 'booting'
                        
        await self.send_data({
            'id': self.identifier,
            'ts': self.ts_started,
            'status': status,
            'busy_queue': shared.state.job_count
        }, channel=channel)
    
    async def request_api(self, task, params, method, chan_name, request_id):
        url = f'http://127.0.0.1:{cmd_opts.port}/sdapi/v1{task}'
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == 'GET':
                    async with session.get(url, params=params) as resp:
                        r = resp
                elif method == 'POST':
                    async with session.post(url, json=params) as resp:
                        r = resp
                else:
                    async with session.get(url, params=params) as resp:
                        r = resp
                
                if r.status == 200:
                    data = await r.json()
                    print(data)
                    await self.send_data(data, True, request_id, chan_name)
                else:
                    data = await r.text()
                    await self.send_data(data, False, request_id, chan_name)
        except Exception as e:
            await self.send_data(str(e), False, request_id, chan_name)
    
    async def handle_global_call(self, msg: PubSub):
        if msg['channel'] != self.global_chan:
            return False
        
        await self.ping_status()
        return True

    async def handle_tasks(self, msg: PubSub):
        data = json.loads(msg['data'])
        
        chan_name = data['from']
        request_id = data['requestId']
        
        try:
            task_name = data['data']['task']
            task_params = data['data']['params']
            task_method = data['data']['method']
        except Exception as e:
            await self.send_data(str(e), False, request_id, chan_name)
            return
        
        if task_name.startswith('/'):
            await self.request_api(task_name, task_params, task_method, chan_name, request_id)
        else:
            await self.ping_status(chan_name)
    
    async def process_message(self, msg: PubSub):
        if msg['type'] not in ['subscribe', 'message']:
            return
        
        if not isinstance(msg['data'], str):
            print(msg)
            return
        
        if await self.handle_global_call(msg):
            return
        
        await self.handle_tasks(msg)
    
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
        asyncio.run(self.launch_async())