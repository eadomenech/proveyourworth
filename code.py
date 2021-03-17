import requests
import hashlib
from requests.structures import CaseInsensitiveDict
from pathlib import Path

import numpy as np
import cv2
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw
from copy import deepcopy


def sha256Binary(key):
    hexa_data = hashlib.sha256(repr(key).encode('utf-8')).hexdigest()
    sha_data = ("{0:8b}".format(int(hexa_data, 16)))
    for v in range(256-(len(sha_data))):
        sha_data = '0' + sha_data
    return sha_data


class BlocksImage():
    def __init__(self, matrix, sblock_rows=8, sblock_cols=8):
        self.matrix = matrix
        self.size_block_rows = sblock_rows
        self.size_block_cols = sblock_cols
        self.blocks_in_cols = len(self.matrix) // self.size_block_rows
        self.blocks_in_rows = len(self.matrix[1]) // self.size_block_cols

    def get(self):
        return self.matrix

    def max_num_blocks(self):
        return self.blocks_in_rows * self.blocks_in_cols

    def image_size(self):
        return self.matrix.shape

    def get_coord(self, num_block):
        # Se cuentan los bloques a partir de 0
        if num_block < self.max_num_blocks():
            L = []
            x1 = num_block // self.blocks_in_rows
            y1 = num_block % self.blocks_in_rows
            L.append(x1 * self.size_block_rows)
            L.append(y1 * self.size_block_cols)
            L.append((x1 + 1) * self.size_block_rows)
            L.append((y1 + 1) * self.size_block_cols)
            return L
        raise Exception("There is no such block")

    def get_block(self, num_block):
        try:
            pos = self.get_coord(num_block)
            return self.matrix[pos[0]:pos[2], pos[1]:pos[3]]
        except Exception:
            return None

    def set_block(self, block, num_block):
        pos = self.get_coord(num_block)
        self.matrix[pos[0]:pos[2], pos[1]:pos[3]] = block


class Avila2019():
    """
    Método de marca de agua digital frágil para imágenes RGB
    """
    def insert(self, cover_image):
        # Image to array
        cover_array = np.array(cover_image)
        # Blue component
        blue_cover_array = cover_array[:, :, 2]
        # Dividing in 32x32 blocks
        blocks32x32 = BlocksImage(blue_cover_array, 32, 32)
        # Touring each block 32x32
        for num_block in range(blocks32x32.max_num_blocks()):
            # Copying block 32x32
            blocksCopy32x32 = deepcopy(blocks32x32.get_block(num_block))
            # Dividing in 16x16 blocks
            blocksCopy16x16 = BlocksImage(blocksCopy32x32, 16, 16)
            # Get first block
            first_block = blocksCopy16x16.get_block(0)
            # Pariar
            for i in range(16):
                for y in range(16):
                    if (first_block[i, y] % 2) == 1:
                        first_block[i, y] -= 1
            # Hash of blocksCopy32x32 pareado
            blocksHash = sha256Binary(blocksCopy32x32.tolist())
            # Insert data
            for i in range(16):
                for y in range(16):
                    first_block[i, y] += int(blocksHash[16*i + y])
            # Update block
            blocks32x32.set_block(blocksCopy32x32, num_block)
        watermarked_image = Image.fromarray(cover_array)
        return watermarked_image

    def extract(self, watermarked_image):
        # To array
        watermarked_array = np.asarray(watermarked_image)
        # Blue component
        blue_watermarked_array = watermarked_array[:, :, 2]
        blue_watermarked_array_noise = blue_watermarked_array.copy()
        # Dividing in 32x32 blocks
        blocks32x32 = BlocksImage(blue_watermarked_array_noise, 32, 32)
        # Touring each block 32x32
        modifiedBlocks = []
        for num_block in range(blocks32x32.max_num_blocks()):
            # Copying block 32x32
            blockCopy32x32 = deepcopy(blocks32x32.get_block(num_block))
            # Dividing in 16x16 blocks
            blocksCopy16x16 = BlocksImage(blockCopy32x32, 16, 16)
            # Get first block
            first_block = blocksCopy16x16.get_block(0)
            # Watermark
            w = ''
            # Pariar
            for i in range(16):
                for y in range(16):
                    if (first_block[i, y] % 2) == 1:
                        first_block[i, y] -= 1
                        w += '1'
                    else:
                        w += '0'
            # Hash of blocksCopy32x32 pareado
            blocksHash = sha256Binary(blockCopy32x32.tolist())
            if w != blocksHash:
                modifiedBlocks.append(num_block)
        for item in modifiedBlocks:
            coord = blocks32x32.get_coord(item)
            cv2.rectangle(
                watermarked_array, (coord[1], coord[0]),
                (coord[3], coord[2]), (0, 255, 0), 1)
        return Image.fromarray(watermarked_array), modifiedBlocks


URL = 'https://www.proveyourworth.net/level3/'
email = 'test@gmail.com'
name = 'Test'
aboutme = "I’m a Python developer. Mainly, my experience is in " +\
    "Python, mostly web development with Django, Web2py and Flask. " +\
    "I am a hardworking and responsible person. I love soccer and I " +\
    "don't dance."
file_path = Path("./")
params = {}
headers = CaseInsensitiveDict()
session = requests.Session()
wm = Avila2019()


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
    img.save('image.jpg', quality=90)

    cover_image = Image.open('image.jpg').convert('RGB')
    watermarked_image = wm.insert(cover_image)
    watermarked_image.save("image.png")

    return post_url


def post_back_to(post_url):
    files = {
        'image': open(file_path / "image.png", "rb"),
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
