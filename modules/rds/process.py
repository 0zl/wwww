import modules.rds.utils as rds_utils
import modules.shared as shared

from threading import Lock
from modules import sd_samplers, deepbooru, sd_hijack, images, scripts, ui, postprocessing, errors, restart, shared_items

def script_name_to_index(name, scripts):
    try:
        return [script.title().lower() for script in scripts].index(name.lower())
    except Exception as e:
        raise ValueError(f"Script '{name}' not found") from e

def validate_sampler_name(name):
    config = sd_samplers.all_samplers_map.get(name, None)
    if config is None:
        raise ValueError(f"Sampler '{name}' not found")

    return name

# TODO: setUpscalers

class RDSProcessor:
    queue_lock: Lock
    default_script_arg_txt2img: list
    default_script_arg_img2img: list
    
    def __init__(self, queue_lock: Lock):
        self.queue_lock = queue_lock
        self.default_script_arg_txt2img = []
        self.default_script_arg_img2img = []