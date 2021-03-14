# -*- coding: utf-8 -*-
from fragilWatermarking.method_Avila2019 import Avila2019

from tkinter import filedialog
from tkinter import *

from PIL import Image


def main():
    # Avila2019 Instances
    wm = Avila2019()

    try:
        # Load watermarked image
        root = Tk()
        root.filename = filedialog.askopenfilename(
            initialdir="static/", title="Select file",
            filetypes=(
                ("png files", "*.png"), ("jpg files", "*.jpg"),
                ("all files", "*.*")))
        watermarked_image = Image.open(root.filename)
        root.destroy()

        # Extract
        tampered_image = wm.extract(watermarked_image)
        tampered_image[0].save("static/tampered_image.png")

    except Exception as e:
        root.destroy()
        print("Error: ", e)
        print("The image file was not loaded")


if __name__ == '__main__':
    main()
