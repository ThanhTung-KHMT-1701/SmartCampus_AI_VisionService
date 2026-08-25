import requests, base64, io
from PIL import Image, ImageDraw

URL = 'http://127.0.0.1:8000/vision/face-match'
HDR = {'Authorization': 'Bearer local-dev-token-vision'}
TS = '2026-08-25T07:42:40Z'


def face_a():
    img = Image.new('RGB', (200, 200), (220, 200, 180))
    d = ImageDraw.Draw(img)
    d.ellipse([20, 5, 180, 95], fill=(40, 30, 20))
    d.ellipse([45, 50, 155, 175], fill=(240, 220, 200))
    d.ellipse([70, 90, 90, 105], fill=(255, 255, 255))
    d.ellipse([75, 92, 85, 102], fill=(40, 40, 80))
    d.ellipse([110, 90, 130, 105], fill=(255, 255, 255))
    d.ellipse([115, 92, 125, 102], fill=(40, 40, 80))
    d.polygon([(95, 110), (105, 110), (100, 135)], fill=(210, 180, 160))
    d.ellipse([82, 145, 118, 160], fill=(180, 60, 60))
    buf = io.BytesIO(); img.save(buf, 'JPEG', quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def face_b():
    img = Image.new('RGB', (200, 200), (200, 180, 150))
    d = ImageDraw.Draw(img)
    d.ellipse([10, 0, 190, 80], fill=(180, 80, 40))
    d.ellipse([40, 45, 160, 180], fill=(255, 240, 220))
    d.ellipse([60, 80, 100, 110], fill=(255, 255, 255))
    d.ellipse([70, 88, 90, 105], fill=(20, 80, 20))
    d.ellipse([100, 80, 140, 110], fill=(255, 255, 255))
    d.ellipse([110, 88, 130, 105], fill=(20, 80, 20))
    d.polygon([(95, 115), (105, 115), (100, 140)], fill=(230, 200, 180))
    d.ellipse([70, 140, 130, 170], fill=(220, 30, 30))
    buf = io.BytesIO(); img.save(buf, 'JPEG', quality=85)
    return base64.b64encode(buf.getvalue()).decode()


A = face_a()
B = face_b()
assert A != B

for name, body in [
    ('A vs A (same)', {'image_base64': A, 'reference_image_base64': A, 'threshold': 0.75, 'timestamp': TS, 'trace_id': 't1'}),
    ('B vs B (same)', {'image_base64': B, 'reference_image_base64': B, 'threshold': 0.75, 'timestamp': TS, 'trace_id': 't2'}),
    ('A vs B (DIFFERENT)', {'image_base64': A, 'reference_image_base64': B, 'threshold': 0.75, 'timestamp': TS, 'trace_id': 't3'}),
    ('A vs B (DIFFERENT, high thresh)', {'image_base64': A, 'reference_image_base64': B, 'threshold': 0.95, 'timestamp': TS, 'trace_id': 't4'}),
]:
    r = requests.post(URL, headers=HDR, json=body, timeout=20)
    j = r.json()
    msg = j.get('message')
    print(f'{name}: HTTP {r.status_code}  matched={j.get("matched")}  conf={j.get("confidence")}  status={j.get("status")}')
    print(f'  msg={msg!r}')
