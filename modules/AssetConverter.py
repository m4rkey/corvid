import os
from os.path import splitext, exists
os.environ["NO_BPY"] = "1"
from PIL import Image, ImageDraw, ImageFont, ImageOps
from SourceIO.source1.vtf.VTFWrapper import VTFLib
from .Vector2 import Vector2
from .Vector3 import Vector3
from tempfile import gettempdir
from .Static import newPath
from PyCoD import Model
from .ModelConverter import convertModel

tempDir = gettempdir() + "/corvid"

def convertImage(src, dest, format="rgba", invert=False, resize=False):
    if not exists(src):
        print(f"{src} could not be found")
        return False
    format = format.upper()
    image = VTFLib.VTFLib()
    image.image_load(src)
    width = image.width()
    height = image.height()
    rgba = Image.frombuffer("RGBA", (width, height), image.convert_to_rgba8888().contents)
    if rgba.size[0] < 4 or rgba.size[1] < 4:
        x = max(rgba.size[0], 4)
        y = max(rgba.size[1], 4)
        rgba.resize((x, y))
    if resize:
        rgba.resize((512, 512))
    if invert:
        rgba = ImageOps.invert(rgba.convert("RGB"))
    if format == "RGBA":
        rgba.save(dest)
    elif format == "RGB":
        rgba.convert("RGB").save(dest)
    elif len(format) == 1:
        rgba.getchannel(format).save(dest)

def convertImages(images, src, dest, ext="tga"):
    images["colorMaps"] = list(dict.fromkeys(images["colorMaps"]))
    images["colorMapsAlpha"] = list(dict.fromkeys(images["colorMapsAlpha"]))
    images["normalMaps"] = list(dict.fromkeys(images["normalMaps"]))
    images["envMaps"] = list(dict.fromkeys(images["envMaps"]))
    images["envMapsAlpha"] = list(dict.fromkeys(images["envMapsAlpha"]))
    images["revealMaps"] = list(dict.fromkeys(images["revealMaps"]))

    lencolorMaps = len(images["colorMaps"]) 
    lencolorMapsAlpha = len(images["colorMapsAlpha"]) 
    lennormalMaps = len(images["normalMaps"]) 
    lenenvMaps = len(images["envMaps"]) 
    lenenvMapsAlpha = len(images["envMapsAlpha"]) 
    lenrevealMaps = len(images["revealMaps"])
    total = lencolorMaps + lencolorMapsAlpha + lennormalMaps + lenenvMaps + lenenvMapsAlpha + lenrevealMaps

    for i, file in enumerate(images["colorMapsAlpha"]):
        print(f"{i}|{total}|done", end="")
        convertImage(f"{tempDir}/{src}/{file}.vtf", f"{tempDir}/converted/{dest}/{file}.{ext}", "rgba")
    for i, file in enumerate(images["normalMaps"], lencolorMapsAlpha):
        print(f"{i}|{total}|done", end="")
        convertImage(f"{tempDir}/{src}/{file}.vtf", f"{tempDir}/converted/{dest}/{file}.{ext}", "rgb")
    for i, file in enumerate(images["envMaps"], lencolorMapsAlpha + lennormalMaps):
        print(f"{i}|{total}|done", end="")
        convertImage(f"{tempDir}/{src}/{file}.vtf", f"{tempDir}/converted/{dest}/{file}.{ext}", "rgb")
    for i, file in enumerate(images["envMapsAlpha"], lencolorMapsAlpha + lennormalMaps + lenenvMaps):
        print(f"{i}|{total}|done", end="")
        convertImage(f"{tempDir}/{src}/{file}.vtf", f"{tempDir}/converted/{dest}/{file}_.{ext}", "a")
    for i, file in enumerate(images["revealMaps"], lencolorMapsAlpha + lennormalMaps + lenenvMaps + lenenvMapsAlpha):
        print(f"{i}|{total}|done", end="")
        convertImage(f"{tempDir}/{src}/{file}.vtf", f"{tempDir}/converted/{dest}/{file}.{ext}", "g", True)
    for i, file in enumerate(images["colorMaps"], lencolorMapsAlpha + lennormalMaps + lenenvMaps + lenenvMapsAlpha + lenrevealMaps):
        print(f"{i}|{total}|done", end="")
        convertImage(f"{tempDir}/{src}/{file}.vtf", f"{tempDir}/converted/{dest}/{file}.{ext}", "rgb")

    # create 404 image for the textures that aren't found
    h = 512
    w = 512
    img = Image.new("RGB", (h,w), (255, 0, 0)) # create a new 15x15 image
    pixels = img.load() # create the pixel map

    col1, col2 = (255, 0, 255), (0, 255, 0)

    box_size = 64
    for i in range (0, h, box_size):
        for j in range(0, w, box_size):
            y, x = i // box_size, j // box_size
            if (y&1)^(x&1):
                for di in range(box_size):
                    for dj in range(box_size):
                        pixels[i+di,j+dj] = col1
            else:
                for di in range(box_size):
                    for dj in range(box_size):
                        pixels[i+di,j+dj] = col2


    draw = ImageDraw.Draw(img)

    draw.text((62, 206), "TEXTURE NOT FOUND", (255, 255, 255), font=ImageFont.truetype("impact.ttf", 50))

    img.save(f"{tempDir}/converted/{dest}/404.{ext}")

def getTexSize(src):
    image = VTFLib.VTFLib()
    image.image_load(src)
    return Vector2(image.width(), image.height())

def convertModels(models, modelTints, modelSkins, skinTints, game="WaW", scale=1.0):
    codModel = Model()
    mdlDir = f"{tempDir}/mdl"
    convertDir = f"{tempDir}/converted/model_export/corvid"
    total = len(models)

    for i, model in enumerate(models):
        print(f"{i}|{total}|done", end="")
        model = splitext(newPath(model))[0]
        # convert models with tints
        if game == "BO3" and model in modelTints:
            for tint in modelTints[model]:
                hex = Vector3.FromStr(tint).toHex()
                convertModel(f"{mdlDir}/{model}", convertDir, tint=hex, scale=scale)
                try:
                    codModel.LoadFile_Raw(f"{convertDir}/{model}_{hex}.xmodel_export")
                    codModel.WriteFile_Bin(f"{convertDir}/{model}_{hex}.xmodel_bin")
                except:
                    print(f"Could not convert {model}_{hex} to xmodel_bin...")
                else:
                    os.remove(f"{convertDir}/{model}_{hex}.xmodel_export")
        convertModel(f"{mdlDir}/{model}", convertDir, scale=scale)

        # convert models with skins
        if model in modelSkins:
            for skin in modelSkins[model]:
                convertModel(f"{mdlDir}/{model}", convertDir, skin=skin, scale=scale)
                if game == "BO3":
                    try:
                        codModel.LoadFile_Raw(f"{convertDir}/{model}_skin{skin}.xmodel_export")
                        codModel.WriteFile_Bin(f"{convertDir}/{model}_skin{skin}.xmodel_bin")
                    except:
                        print(f"Could not convert {model} to xmodel_bin...")
                    else:
                        os.remove(f"{convertDir}/{model}_skin{skin}.xmodel_export")
        
        if game == "BO3" and  model in skinTints:
            for skin, tints in skinTints[model].items():
                for tint in tints:
                    hex = Vector3.FromStr(tint).toHex()
                    convertModel(f"{mdlDir}/{model}", convertDir, hex, skin, scale)
                    try:
                        codModel.LoadFile_Raw(f"{convertDir}/{model}_skin{skin}_{hex}.xmodel_export")
                        codModel.WriteFile_Bin(f"{convertDir}/{model}_skin{skin}_{hex}.xmodel_bin")
                    except:
                        print(f"Could not convert {model} to xmodel_bin...")
                    else:
                        os.remove(f"{convertDir}/{model}_skin{skin}_{hex}.xmodel_export")



        if game == "BO3":
            try:
                codModel.LoadFile_Raw(f"{convertDir}/{model}.xmodel_export")
                codModel.WriteFile_Bin(f"{convertDir}/{model}.xmodel_bin")
            except:
                print(f"Could not convert {model} to xmodel_bin...")
            else:
                os.remove(f"{convertDir}/{model}.xmodel_export")
