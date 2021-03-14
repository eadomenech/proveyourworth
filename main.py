import requests
from requests.structures import CaseInsensitiveDict

from bs4 import BeautifulSoup
from PIL import Image
from PIL import ImageDraw 

from fragilWatermarking.method_Avila2019 import Avila2019


URL = 'https://www.proveyourworth.net/level3/'
username = 'Test1'
params = {}
headers = CaseInsensitiveDict()
session = requests.Session()
print(f"Headers: {headers}")
print(f"Cookie: {session.cookies.get_dict()}")
success = False

# Avila2019 Instances
wm = Avila2019()

while not success:
    # Get a página inicial
    r = session.get(f"{URL}")
    print(f"GET a: {r.url}")
    if r.status_code == 200:
        print(f"Headers: {r.headers}")
        print(f"Cookie: {session.cookies.get_dict()}")
        soup = BeautifulSoup(r.text)
        inputs = soup.find("input")
        if inputs:
            params['statefulhash'] = inputs['value']
            print(f"Obteniendo statefulhash: {params['statefulhash']}")
            params['username'] = username
            print(f"Headers: {headers}")
            url_activate = URL + 'activate'
            res = session.get(url_activate, headers=headers, params=params)
            print(f"GET a: {res.url}")
            print(f"Headers: {res.headers}")
            print(f"Cookie: {session.cookies.get_dict()}")
            if 'X-Payload-URL' in res.headers:
                payload_url = res.headers['X-Payload-URL']
                print(f"Payload URL: {payload_url}")
                success = True

success = False
while not success:
    response_payload = session.get(payload_url)
    print(f"GET a: {response_payload.url}")
    if response_payload.status_code == 200:
        file = open("static/bmw_for_life.jpg", "wb")
        file.write(response_payload.content)
        file.close()
        print(f"headers: {response_payload.headers}")
        success = True

img = Image.open("static/bmw_for_life.jpg")
draw = ImageDraw.Draw(img)
draw.text(
    (img.size[0] - 50, img.size[1] - 50),
    username, (255,255,255))
img.save('static/signed_bmw_for_life.jpg', quality=90)

cover_image = Image.open(
    'static/signed_bmw_for_life.jpg').convert('RGB')
watermarked_image = wm.insert(cover_image)
watermarked_image.save("static/watermarked_signed_bmw_for_life.png")