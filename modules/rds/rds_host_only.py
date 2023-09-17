import redis, json, requests, time
from redis.client import PubSub
from modules.shared_cmd_options import cmd_opts
from modules import shared


def serialize(identifier, data, requestId=None, callbackId=None):
    timestamp = int(round(time.time() * 1000))
    return json.dumps({
        'ts': timestamp,
        'from': identifier,
        'data': data,
        'requestId': requestId,
        'callbackId': callbackId
    })


class RDSClient:
    client: redis.Redis = None
    pcl: PubSub = None
    
    def __init__(self):
        self.host = cmd_opts.rds_h
        self.port = cmd_opts.rds_p
        self.secret = cmd_opts.rds_secret
        self.identifier = cmd_opts.rds_id
        self.mother = cmd_opts.rds_mother
        self.global_chan = cmd_opts.rds_global
        self.ts_started = int(round(time.time() * 1000))
    
    def launch(self):
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            password=self.secret,
            decode_responses=True
        )
        
        self.pubsub()
    
    def send_data(self, data, success=True, requestId=None, channel=None):
        if hasattr(data, '__dict__'):
            data = data.__dict__
        elif type(data) is list:
            list_data = []
            for i, e in enumerate(data):
                list_data.append(e)
            data = { 'list': list_data }
        else:
            data = { 'info': data }
        
        n_data = { 'success': success, **data }
        self.client.publish(
            self.mother if channel is None else channel,
            serialize(self.identifier, n_data, callbackId=requestId)
        )
    
    def ping_status(self, channel=None):
        url = f'http://127.0.0.1:{cmd_opts.port}'
        check = requests.head(url)
        
        if check.status_code == 200:
            status = 'online'
        else:
            if shared.is_model_ready:
                status = 'offline'
            else:
                status = 'booting'
        
        self.send_data({
            'id': self.identifier,
            'ts': self.ts_started,
            'status': status
        }, channel=channel)
    
    def request_api(self, task, params, method, chan_name, request_id):
        url = f'http://127.0.0.1:{cmd_opts.port}/sdapi/v1{task}'

        r = requests(url, json=params, method=method)
            
        if r.status_code == 200:
            data = r.json()
            self.send_data(data, True, request_id, chan_name)
        else:
            data = r.text()
            self.send_data(data, False, request_id, chan_name)

        # try:
        #     r = requests(url, json=params, method=method)
            
        #     if r.status_code == 200:
        #         data = r.json()
        #         self.send_data(data, True, request_id, chan_name)
        #     else:
        #         data = r.text()
        #         self.send_data(data, False, request_id, chan_name)
        # except Exception as e:
        #     self.send_data(str(e), False, request_id, chan_name)

        print(f'chan_name: {chan_name}, requestId: {request_id}')
        
    def handle_global_call(self, msg):
        print(msg)
        if msg['channel'] != self.global_chan:
            return False

        self.ping_status()
        return True

    def handle_tasks(self, msg):
        data = json.loads(msg['data'])
        
        chan_name = data['from']
        request_id = data['requestId']
            
        try:
            task_name = data['data']['task']
            task_params = data['data']['params']
            task_method = data['data']['method']
        except Exception as e:
            self.send_data(str(e), False, request_id, chan_name)
            return
            
        if task_name.startswith('/'):
            self.request_api(task_name, task_params, task_method, chan_name, request_id)
        else:
            self.ping_status(chan_name)
    
    def pubsub(self):
        self.pcl = self.client.pubsub()
        self.pcl.subscribe(self.identifier)
        self.pcl.subscribe(self.global_chan)
        
        self.send_data('online')
        print('nya~~~~~~~~~~~~~~~~~~~~~~~')
        
        for msg in self.pcl.listen():
            if msg['type'] not in ['subscribe', 'message']:
                continue
            
            if not isinstance(msg['data'], str):
                print(msg)
                continue
            
            if self.handle_global_call(msg):
                continue
            
            self.handle_tasks(msg)