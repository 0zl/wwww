import redis, json

from modules.call_queue import queue_lock
from modules.rds.process import RDSProcessor

processor = RDSProcessor(queue_lock)

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
            
            data = json.loads(msg['data'])
            print(data)
            