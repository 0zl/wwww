import redis

class RDS:
    client = None
    
    host = None
    port = None
    password = None
    identifier = None
    root_path = None
    
    def __init__(self, host, port, password, identifier, root_path):
        self.host = host
        self.port = port
        self.password = password
        self.identifier = identifier
        self.root_path = root_path
    
    def launch(self):
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            password=self.password,
            decode_responses=True
        )