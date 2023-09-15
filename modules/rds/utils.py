import base64
from PIL import Image, PngImagePlugin
from io import BytesIO

def decode_base64_to_image(data):
    try:
        return Image.open(
            BytesIO(base64.b64decode(data))
        )
    except Exception as e:
        raise ValueError("Invalid encoded image") from e

# will default encode from PNG.
def encode_pil_to_base64(image):
    with BytesIO() as output_bytes:
        use_metadata = False
        metadata = PngImagePlugin.PngInfo()
        
        for k, v in image.info.items():
            if isinstance(k, str) and isinstance(v, str):
                metadata.add_text(k, v)
                use_metadata = True
        
        image.save(output_bytes, format="PNG", pnginfo=(metadata if use_metadata else None), quality=100)
        bytes_data = output_bytes.getvalue()

    return base64.b64encode(bytes_data)