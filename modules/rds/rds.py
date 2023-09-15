import io, os, time, datetime, ipaddress, redis
import modules.shared as shared
import modules.devices as devices

from modules.shared import opts
from modules.processing import StableDiffusionProcessingTxt2Img, StableDiffusionProcessingImg2Img, process_images

class RDS:
    client = None
    pcl = None
    
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
        
        self.pubsub()
    
    def pubsub(self):
        self.pcl = self.client.pubsub()
        self.pcl.subscribe(self.identifier)
        
        for msg in self.pcl.listen():
            print(msg)