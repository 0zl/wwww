import redis, json
import modules.rds.utils as rds_utils

from redis.client import PubSub
from modules.call_queue import queue_lock
from modules.rds.process import RDSProcessor

processor = RDSProcessor(queue_lock)

available_tasks = [
    { 'task': 'memory', 'arg_pass': False, 'method': processor.get_memory },
    { 'task': 'get_config', 'arg_pass': False, 'method': processor.get_config },
    { 'task': 'set_config', 'arg_pass': True, 'method': processor.set_config },
    { 'task': 'get_cmd_flags', 'arg_pass': False, 'method': processor.get_cmd_flags },
    { 'task': 'get_samplers', 'arg_pass': False, 'method': processor.get_samplers },
    { 'task': 'get_sd_models', 'arg_pass': False, 'method': processor.get_sd_models },
    { 'task': 'get_sd_vaes', 'arg_pass': False, 'method': processor.get_sd_vaes },
    { 'task': 'refresh_checkpoints', 'arg_pass': False, 'method': processor.refresh_checkpoints },
    { 'task': 'refresh_vae', 'arg_pass': False, 'method': processor.refresh_vae },
    { 'task': 'kill', 'arg_pass': False, 'method': processor.kill },
    { 'task': 'restart', 'arg_pass': False, 'method': processor.restart },
    { 'task': 'txt2img', 'arg_pass': True, 'method': processor.text2imgapi },
    { 'task': 'img2img', 'arg_pass': True, 'method': processor.img2imgapi }
]

def get_task(task_name):
    for task in available_tasks:
        if task['task'] == task_name:
            return task
    return None

class RDS:
    client = None
    pcl: PubSub = None
    
    host = None
    port = None
    password = None
    identifier = None
    mother = None # ayooo
    root_path = None
    global_chan = 'wwwwfx'
    
    def __init__(self, host, port, password, identifier, mother, root_path):
        self.host = host
        self.port = port
        self.password = password
        self.identifier = identifier
        self.mother = mother
        self.root_path = root_path
    
    def launch(self):
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            password=self.password,
            decode_responses=True
        )
        
        self.pubsub()
    
    def publish_data(self, data, is_success, requestId=None, channel=None):
        n_data = { 'success': is_success, **data }
        self.client.publish(
            self.mother if channel is None else channel,
            rds_utils.serialize(self.identifier, n_data, callbackId=requestId)
        )
        
    def pubsub(self):
        self.pcl = self.client.pubsub()
        self.pcl.subscribe(self.identifier)
        self.pcl.subscribe(self.global_chan)
        
        print('nya~')
        self.publish_data({ 'info': 'online' }, True)
        
        for msg in self.pcl.listen():
            if msg['type'] not in ['subscribe', 'message']:
                continue
            
            if not isinstance(msg['data'], str):
                print(msg)
                continue
            
            data = json.loads(msg['data'])
            chan_name = data['from']
            requestId = data['requestId']
            
            print(f'requestId: {requestId}, channel: {chan_name}')
            
            # 'global' channel
            if msg['channel'] == self.global_chan:
                self.publish_data({ 'id': self.identifier }, True, channel=chan_name)
                continue
            
            task_name = data['data']['task']
            task_args = data['data']['args']
            
            task = get_task(task_name)
            if task is None:
                print('task not found')
                continue
            
            try:
                if task['arg_pass']:
                    result = task['method'](task_args)
                else:
                    result = task['method']()
                
                if requestId:
                    if hasattr(result, '__dict__'):
                        result = result.__dict__
                    elif type(result) is list:
                        list_data = []
                        for index, element in enumerate(result):
                            list_data.append(element)
                        result = { 'list': list_data }
                        
                    self.publish_data(result, True, requestId, chan_name)
            except Exception as e:
                print(e)
                if requestId:
                    self.publish_data({ 'error': str(e) }, False, requestId, chan_name)
            