import hashlib
import pycurl
import json
from urllib.parse import urlencode
from io import BytesIO

from bs4 import BeautifulSoup
from PIL import Image, ImageDraw
import numpy as np
from copy import deepcopy
import cv2


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
email = 'tests@gmail.com'
name = 'Test'
params = {}
success = False
wm = Avila2019()
b_obj1 = BytesIO()
b_obj2 = BytesIO()
b_obj3 = BytesIO()
b_obj4 = BytesIO()
headers = {}


def header_function(header_line):
    # HTTP standard specifies that headers are encoded in iso-8859-1.
    # On Python 2, decoding step can be skipped.
    # On Python 3, decoding step is required.
    header_line = header_line.decode('iso-8859-1')

    # Header lines include the first status line (HTTP/1.x ...).
    # We are going to ignore all lines that don't have a colon in them.
    # This will botch headers that are split on multiple lines...
    if ':' not in header_line:
        return

    # Break the header line into header name and value.
    name, value = header_line.split(':', 1)

    # Remove whitespace that may be present.
    # Header lines include the trailing newline, and there may be whitespace
    # around the colon.
    name = name.strip()
    value = value.strip()

    # Header names are case insensitive.
    # Lowercase name here.
    name = name.lower()

    # Now we can actually record the header name and value.
    # Note: this only works when headers are not duplicated, see below.
    headers[name] = value


while not success:

    crl = pycurl.Curl()

    # Set URL value
    crl.setopt(crl.URL, URL)

    # Write bytes that are utf-8 encoded
    crl.setopt(crl.WRITEDATA, b_obj1)

    # Set our header function.
    crl.setopt(crl.HEADERFUNCTION, header_function)

    # Perform a file transfer
    crl.setopt(pycurl.COOKIEJAR, 'cookie1.txt')
    crl.perform()

    # HTTP response code, e.g. 200.
    status_code = crl.getinfo(crl.RESPONSE_CODE)
    print('Status: %d' % status_code)

    # End curl session
    crl.close()

    print(f"Headers: {headers}")
    headers = {}

    if status_code == 200:
        # Get statefulhash
        soup = BeautifulSoup(b_obj1.getvalue())
        inputs = soup.find("input")
        if inputs:
            params['username'] = name
            print(f"Name: {params['username']}")
            params['statefulhash'] = inputs['value']
            print(f"Statefulhash: {params['statefulhash']}")
            url_activate = URL + 'activate' + '?' + urlencode(params)

            crl = pycurl.Curl()

            # Set URL value
            crl.setopt(crl.URL, url_activate)
            
            # Write bytes that are utf-8 encoded
            crl.setopt(crl.WRITEDATA, b_obj2)

            # Set our header function.
            crl.setopt(crl.HEADERFUNCTION, header_function)

            # Perform a file transfer
            crl.setopt(pycurl.COOKIEFILE, 'cookie1.txt')
            crl.setopt(pycurl.COOKIEJAR, 'cookie2.txt')
            crl.perform()
            
            # End curl session
            crl.close()

            print('Status: %d' % status_code)
            print(f"Headers: {headers}")
            if 'x-payload-url' in headers:
                payload_url = headers['x-payload-url']
                print(f"x-payload-url: {payload_url}")
                success = True
                headers = {}

crl = pycurl.Curl()

# Set URL value
crl.setopt(crl.URL, payload_url)

# Follow redirect.
crl.setopt(crl.FOLLOWLOCATION, True)

# Write bytes that are utf-8 encoded
crl.setopt(crl.WRITEDATA, b_obj3)

# Set our header function.
crl.setopt(crl.HEADERFUNCTION, header_function)

# Perform a file transfer
crl.setopt(pycurl.COOKIEFILE, 'cookie2.txt')
crl.setopt(pycurl.COOKIEJAR, 'cookie3.txt')
crl.perform()

# HTTP response code, e.g. 200.
status_code = crl.getinfo(crl.RESPONSE_CODE)

# End curl session
crl.close()

if 'x-post-back-to' in headers:
    post_url = headers['x-post-back-to']
    print(f"x-post-back-to: {post_url}")

print('Status: %d' % status_code)
print(f"Headers: {headers}")
headers = {}

if status_code == 200:
    file = open("bmw_for_life.jpg", "wb")
    file.write(b_obj3.getvalue())
    file.close()
    success = True

img = Image.open("bmw_for_life.jpg")
draw = ImageDraw.Draw(img)
draw.text(
    (img.size[0] - 250, img.size[1] - 50), name, (255, 255, 255))
img.save('signed_bmw_for_life.jpg', quality=90)

cover_image = Image.open(
    'signed_bmw_for_life.jpg').convert('RGB')
watermarked_image = wm.insert(cover_image)
watermarked_image.save("watermarked_signed_bmw_for_life.png")

crl = pycurl.Curl()
crl.setopt(crl.URL, post_url)

# Follow redirect.
crl.setopt(crl.FOLLOWLOCATION, True)

# Write bytes that are utf-8 encoded
crl.setopt(crl.WRITEDATA, b_obj4)

data = {
    'email': email, 'name': name, 'aboutme': 'I am a Python developer.',
    'image': 'image', 'resume': 'resume', 'code': 'code'}

pf = urlencode(data)
p = json.dumps(data)

crl.setopt(pycurl.POST, 1)
crl.setopt(crl.POSTFIELDS, p)

crl.setopt(crl.HTTPPOST, [
    ('image', (
        # TO-DO use martermaked image
        # Upload the contents of the file
        crl.FORM_FILE, './signed_bmw_for_life.jpg',
    )),
    ('code', (
        # Upload the contents of the file
        crl.FORM_FILE, './resources/code.rar',
    )),
    ('resume', (
        # Upload the contents of the file
        crl.FORM_FILE, './CV/cv.pdf',
    )),
    ('aboutme', (
        # Upload the contents of the file
        crl.FORM_FILE, './aboutme.txt',
    )),
])
# Set our header function.
crl.setopt(crl.HEADERFUNCTION, header_function)

# Perform a file transfer
crl.setopt(pycurl.COOKIEFILE, 'cookie3.txt')
crl.perform()

# HTTP response code, e.g. 200.
status_code = crl.getinfo(crl.RESPONSE_CODE)
print('Status: %d' % status_code)
print(f"Headers: {headers}")
print(f"Body: {b_obj4.getvalue()}")

# End curl session
crl.close()
