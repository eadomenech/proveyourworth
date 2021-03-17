import requests
from requests.structures import CaseInsensitiveDict
from pathlib import Path

from bs4 import BeautifulSoup
from PIL import Image, ImageDraw


URL = 'https://www.proveyourworth.net/level3/'
email = 'eadomenech@gmail.com'
name = 'Ernesto Avila Domenech'
aboutme = "I’m a Python developer. Mainly, my experience is in " +\
    "Python, mostly web development with Django, Web2py and Flask. " +\
    "I am a hardworking and responsible person. I love soccer and I " +\
    "don't dance."
file_path = Path("./")
params = {}
headers = CaseInsensitiveDict()
session = requests.Session()


def get_payload_url():
    while True:
        response = session.get(f"{URL}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text)
            inputs = soup.find("input")
            if inputs:
                params['statefulhash'] = inputs['value']
                params['username'] = name
                url_activate = URL + 'activate'
                res = session.get(
                    url_activate, headers=headers, params=params)
                if 'X-Payload-URL' in res.headers:
                    return res.headers['X-Payload-URL']


def download_and_sign_image(payload_url):
    success = False
    while not success:
        response_payload = session.get(payload_url)
        if response_payload.status_code == 200:
            file = open("bmw_for_life.jpg", "wb")
            file.write(response_payload.content)
            file.close()
            post_url = response_payload.headers['X-Post-Back-To']
            success = True

    img = Image.open("bmw_for_life.jpg")
    draw = ImageDraw.Draw(img)
    draw.text(
        (20, 20),
        f"{name} \n Hash:{params['statefulhash']}", (255, 255, 255))
    img.save('image.jpg', "JPEG")

    return post_url


def post_back_to(post_url):
    files = {
        'image': open(file_path / "image.jpg", "rb"),
        'code': open(file_path / "code.py", "rb"),
        'resume': open(file_path / "resume.pdf", "rb")
    }

    data = {'email': email, 'name': name, 'aboutme': aboutme}

    # print(
    #     requests.Request('POST', response_payload.headers['X-Post-Back-To'],
    #     data=data, files=files).prepare().body)

    response = session.post(post_url, data=data, files=files)

    print("Response")
    print(response.url)
    print(response.status_code)
    print(response.text)


if __name__ == '__main__':
    payload_url = get_payload_url()
    post_url = download_and_sign_image(payload_url)
    post_back_to(post_url)
