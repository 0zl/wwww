import redis, json

from modules.call_queue import queue_lock
from modules.rds.process import RDSProcessor

processor = RDSProcessor(queue_lock)

available_tasks = [
    { 'task': 'memory', 'arg_pass': False, 'method': processor.get_memory }
]

def get_task(task_name):
    for task in available_tasks:
        if task['task'] == task_name:
            return task
    return None

class RDS:
    client = None
    pcl = None
    
    host = None
    port = None
    password = None
    identifier = None
    mother = None # ayooo
    root_path = None
    
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
    
    def pubsub(self):
        self.pcl = self.client.pubsub()
        self.pcl.subscribe(self.identifier)
        
        print('nya~')
        for msg in self.pcl.listen():
            if msg['type'] not in ['subscribe', 'message']:
                continue
            
            if not isinstance(msg['data'], str):
                print(msg)
                continue
            
            data = json.loads(msg['data'])
            task_name = data['data']['task']
            task_args = data['data']['args']
            requestId = data['requestId']
            
            print(f'task: {task_name}, args: {task_args}, requestId: {requestId}')
            
            task = get_task(task_name)
            if task is None:
                print('task not found')
                continue
            
            try:
                if task['arg_pass']:
                    result = task['method'](task_args)
                else:
                    result = task['method']()
                
                print(result)
            except Exception as e:
                print(e)
            