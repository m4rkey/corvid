from modules.SourceDir import SourceDir
from modules.AssetConverter import convertImages, convertModels
from .Side import Side
from .MapReader import readMap
from .Vector2 import Vector2
from .Vector3 import Vector3
from .Gdt import Gdt
from os.path import basename, splitext, dirname
from os import makedirs
from sys import exit
from pprint import pprint
from tempfile import gettempdir
from vmf_tool.parser import parse
from .AssetExporter import *

class vertexTable:
    def __init__(self):
        self.table = {}
    
    def add(self, vert: Vector3):
        index = str(int(vert.len()))
        if index in self.table:
            for point in self.table[index]:
                if point == vert:
                    return point
            self.table[index].append(vert)
            return vert
        else:
            self.table[index] = []
            self.table[index].append(vert)
            return vert

def convertSide(side: Side, matSize, table: vertexTable):
    res = ""
    points = []
    # get uv points
    for point in side.points:
        points.append(table.add(point))
        side.uvs.append(side.getUV(point, matSize[basename(side.material).strip()]))
    uvs: list[Vector2] = side.uvs

    if len(points) % 2 == 1:
        points.append(points[-1])
        uvs.append(uvs[-1])
    count = len(points)
    rows = int(count / 2)

    if side.material.lower().strip().startswith("liquids"):
        side.material = "clip"

    res += (
        " {\n" +
        "  mesh\n" +
        "  {\n" +
        "   " + basename(side.material).lower().strip() + "\n" +
        "   lightmap_gray\n" +
        "   " + str(rows) + " 2 " + str(side.lightmapScale) + " 8\n"
    )

    for i in range(rows):
        p1 = {
            "pos": str(points[i]),
            "uv": str(uvs[i] * side.texSize),
            "lm": str(uvs[i] * side.lightmapScale)
        }
        p2 = {
            "pos": str(points[count - i - 1]),
            "uv": str(uvs[count - i - 1] * side.texSize),
            "lm": str(uvs[count - i - 1] * side.lightmapScale)
        }
        res += (
            "   (\n" +
            f'    v {p1["pos"]} t {p1["uv"]} {p1["lm"]}\n' +
            f'    v {p2["pos"]} t {p2["uv"]} {p2["lm"]}\n' +
            "   )\n"
        )

    res += (
        "  }\n" +
        " }\n"
    )
    return res


def getDispPoints(p1: Vector3, p2: Vector3, uv1: Vector2, uv2: Vector2, power: int):
    res = []
    rowCount = int(2 ** power) + 1
    for i in range(rowCount):
        res.append({
            "pos": p1.lerp(p2, 1 / (rowCount - 1) * i),
            "uv": uv1.lerp(uv2, 1 / (rowCount - 1) * i)
        })
    return res


def convertDisplacement(side: Side, matSize, table: vertexTable):
    res = ""
    points = []
    # get uv points
    for point in side.points:
        points.append(table.add(point))
        side.uvs.append(side.getUV(point, matSize[basename(side.material).strip()]))

    if len(points) != 4:
        print(f"Displacement has {len(points)}. Displacements can have 4 points only. Side id: {side.id}\n")
        for point in points:
            print(point)
        return ""
    uvs: list[Vector2] = side.uvs
    disp: dict = side.dispinfo
    power: int = int(disp["power"])
    numVerts: int = int(2 ** power) + 1
    s: int = 0
    for i in range(4):
        if points[i] == disp["startpos"]:
            s = i
            break

    a = points[s]
    b = points[(s + 1) % 4]
    c = points[(s + 2) % 4]
    d = points[(s + 3) % 4]

    UVa = uvs[s]
    UVb = uvs[(s + 1) % 4]
    UVc = uvs[(s + 2) % 4]
    UVd = uvs[(s + 3) % 4]

    ab = getDispPoints(a, b, UVa, UVb, power)
    dc = getDispPoints(d, c, UVd, UVc, power)

    rows = []
    for i in range(len(ab)):
        rows.append(
            getDispPoints(ab[i]["pos"], dc[i]["pos"], ab[i]["uv"], dc[i]["uv"], power))

    alpha = False

    res += (
        " {\n" +
        "  mesh\n" +
        "  {\n" +
        "   " + basename(side.material).lower().strip() + "\n" +
        "   lightmap_gray\n"
        "   " + str(len(rows[0])) + " " + str(len(rows[0])
                                              ) + " " + str(side.lightmapScale) + " 8\n"
    )

    for i in range(numVerts):
        row = rows[i]
        res += "   (\n"
        for j in range(numVerts):
            if disp["row"][j]["alphas"][i] != 0 and alpha != True:
                alpha = True
            col = row[j]
            pos = (col["pos"] + Vector3(0, 0, disp["elevation"]) +
                   (disp["row"][j]["normals"][i] * disp["row"][j]["distances"][i]))
            uv = (col["uv"] * side.texSize) * 1
            lm = col["uv"] * (side.lightmapScale)
            res += f"    v {pos} t {uv} {lm}\n"
        res += "   )\n"
    res += ("  }\n" +
            " }\n")

    if not alpha:
        return res
    if basename(side.material).lower().strip() + "_" not in matSize:
        return res

    res += (
        " {\n" +
        "  mesh\n" +
        "  {\n" +
        "   " + basename(side.material).lower().strip() + "_\n" +
        "   lightmap_gray\n" +
        "   " + str(len(rows[0])) + " " + str(len(rows[0])
                                              ) + " " + str(side.lightmapScale) + " 8\n"
    )

    for i in range(numVerts):
        row = rows[i]
        res += "   (\n"
        for j in range(numVerts):
            col = row[j]
            pos = (col["pos"] + Vector3(0, 0, disp["elevation"]) +
                   (disp["row"][j]["normals"][i] * disp["row"][j]["distances"][i]))
            uv = (col["uv"] * side.texSize) * 1
            lm = col["uv"] * (side.lightmapScale)
            if disp["row"][j]["alphas"][i] == 0:
                res += f"    v {pos} c 255 255 255 0 t {uv} {lm}\n"
            else:
                color = "255 255 255 " + str(disp["row"][j]["alphas"][i])
                res += f"    v {pos} c {color} t {uv} {lm}\n"
        res += "   )\n"
    res += ("  }\n" +
            " }\n")

    return res


def convertBrush(brush, world=True):
    classnames = ["func_detail", "func_brush", "func_illusionary", "func_breakable", "func_breakable_surf", "func_door", "func_door_rotating",
                  "func_ladder", "func_door", "func_movelinear", "func_lod", "func_lookdoor", "func_physbox", "func_physbox_multiplayer",
                  "func_rotating", "func_tank", "func_tankairboatgun", "func_tankapcrocket", "func_tanklaser", "func_tankmortar",
                  "func_tankphyscannister", "func_tankpulselaser", "func_tankrocket", "func_tanktrain", "func_trackautochange", "func_trackchange",
                  "func_tracktrain", "func_traincontrols", "func_wall", "func_wall_toggle", "func_water_analog"]
    tools = {
        "toolsnodraw": "caulk",
        "toolsclip": "clip",
        "toolsplayerclip": "clip",
        "toolsinvisible": "clip",
        "toolsinvisibleladder": "clip",
        "toolsnpcclip": "clip",
        "toolsgrenadeclip": "clip_missile",
        "toolsblack": "global_black",
        "toolsareaportal": "portal_nodraw",
        "toolsblocklight": "shadowcaster",
        "toolshint": "hint",
        "toolsskip": "skip",
        "toolsskybox": "sky"
    }

    res = " {\n"
    if not world:
        res += "  contents detail;\n"
    else:
        pass  # do nothing. structural brushes and portals don't need to be specified like detail brushes

    material = ""

    for side in brush.sides:
        if side.material.startswith("tools"):
            mat = basename(side.material)
            if mat not in tools:
                return ""
            else:
                material = tools[mat]
        else:
            material = "caulk"
        res += f"  ( {side.p1} ) ( {side.p2} ) ( {side.p3} ) {material} 128 128 0 0 0 0 lightmap_gray 16384 16384 0 0 0 0\n"

    res += " }\n"
    return res

def convertEntity(entity):
    res = "{\n"
    for key, value in entity.items():
        res += f' "{key}" "{value}"\n'
    res += "}\n"
    return res

def convertLight(entity):
    if "_light" in entity:
        _color = entity["_light"].split(" ")
    else:
        _color = [0, 0, 0, 500]
    # In Radiant, color value of light entities range between 0 and 1 whereas it varies between 0 and 255 in Source engine
    color = Vector3(_color[0], _color[1], _color[2]) / 255
    return convertEntity({
        "classname": "light",
        "origin": entity["origin"],
        "_color": color,
        "radius": 250,
        "intensity": "1"
    })

def convertSpotLight(entity, BO3=False):
    if "_light" in entity:
        _color = entity["_light"].split(" ")
    else:
        _color = [0, 0, 0, 500]
    # In Radiant, color value of light entities range between 0 and 1 whereas it varies between 0 and 255 in Source engine
    color = Vector3(_color[0], _color[1], _color[2]) / 255
    _origin = entity["origin"].split(" ")
    origin = Vector3(_origin[0], _origin[1], _origin[2])
    if "_fifty_percent_distance" in entity and "_zero_percent_distance" not in entity:
        radius = int(entity["_fifty_percent_distance"])
    elif "_zero_percent_distance" in entity and "_fifty_percent_distance" not in entity:
        radius = int(entity["_zero_percent_distance"])
    elif "_fifty_percent_distance" in entity and "_zero_percent_distance" in entity:
        radius = (int(entity["_fifty_percent_distance"]) * 2 + int(entity["_zero_percent_distance"])) / 2
    else:
        radius = 250
    
    if not BO3:
        res = convertEntity({
            "classname": "light",
            "origin": entity["origin"],
            "_color": color,
            "radius": radius,
            "intensity": "1",
            "target": "spotlight_" + entity["id"],
            "fov_outer": entity["_cone"],
            "fov_inner": entity["_inner_cone"],
        })
        res += convertEntity({
            "classname": "info_null",
            "origin": origin + Vector3(0, 0, -float(_color[3])),
            "targetname": "spotlight_" + entity["id"]
        })
    else:
        angles = entity["angles"].split(" ")
        angles = entity["pitch"] + " " + angles[1] + " 0"
        res = convertEntity({
            "classname": "light",
            "origin": entity["origin"],
            "_color": color,
            "PRIMARY_TYPE": "PRIMARY_SPOT",
            "angles": angles,
            "radius": radius,
            "fov_outer": entity["_cone"],
            "fov_inner": entity["_inner_cone"],
        })
    return res

def convertRope(entity):
    res = "";
    if entity["classname"] == "move_rope":
        res += convertEntity({
            "classname": "rope",
            "origin": entity["origin"],
            "target": entity["NextKey"] if "NextKey" in entity else entity["id"],
            "length_scale": float(entity["Slack"]) / 128,
            "width": float(entity["Width"]) * 3
        })
        if "targetname" in entity:
            res += convertEntity({
                "classname": "info_null",
                "origin": entity["origin"],
                "targetname": entity["targetname"] if "targetname" in entity else entity["id"]
            });
    else:
        res += convertEntity({
            "classname": "info_null",
            "origin": entity["origin"],
            "targetname": entity["targetname"]
        })
        if "NextKey" in entity:
            res += convertEntity({
                "classname": "rope",
                "origin": entity["origin"],
                "target": entity["NextKey"],
                "length_scale": float(entity["Slack"]) / 125,
                "width": entity["width"] if "width" in entity else "1"
            })
    return res

def convertProp(entity):
    if "model" not in entity:
        return convertEntity({
            "classname": "info_null",
            "original_classname": entity["classname"]
        })

    return convertEntity({
        "classname": "dyn_model" if entity["classname"].startswith("prop_physics") else "misc_model",
        "model": splitext(basename(entity["model"].lower()))[0],
        "origin": entity["origin"],
        "angles": entity["angles"],
        "spawnflags": "16" if entity["classname"].startswith("prop_physics") else "",
        "modelscale": entity["uniformscale"] if "uniformscale" in entity else entity["modelscale"] if "modelscale" in entity else "1"
    })

def convertCubemap(entity):
    return convertEntity({
        "classname": "reflection_probe",
        "origin": entity["origin"]
    })

def convertSpawner(entity):
    spawners = {
        "info_player_terrorist": "mp_tdm_spawn_axis_start",
        "info_player_counterterrorist": "mp_tdm_spawn_allies_start",
        "info_deathmatch_spawn": "mp_dm_spawn",
        "info_player_start": "info_player_start",
    }
    if entity["classname"] in spawners:
        classname = spawners[entity["classname"]]
    else:
        print(entity["classname"])
        return ""
    res = convertEntity({
        "classname": classname,
        "origin": entity["origin"],
        "angles": entity["angles"]
    })

    if classname == "info_player_start":
        res += convertEntity({
            "classname": "mp_global_intermission",
            "origin": entity["origin"]
        })

    return res

def exportMap(vmfString, BO3=False):
    mapData = readMap(vmfString)

    # create temporary directories to extract assets
    copyDir = gettempdir() + "/corvid"
    try:
        makedirs(f"{copyDir}/mdl")
        makedirs(f"{copyDir}/mat")
        makedirs(f"{copyDir}/mdlMats")
        makedirs(f"{copyDir}/matTex")
        makedirs(f"{copyDir}/mdlTex")
        makedirs(f"{copyDir}/converted/bin")
        makedirs(f"{copyDir}/converted/model_export/corvid")
        makedirs(f"{copyDir}/converted/source_data")
        makedirs(f"{copyDir}/converted/texture_assets/corvid")
    except:
        pass

    # load &/ define the paks and folders where the assets will be grabbed from
    gamePath = SourceDir()
    gamePath.add("C:/stuff/Steam/steamapps/common/Counter-Strike Global Offensive/csgo/pak01_dir.vpk")
    gamePath.add("C:/stuff/Steam/steamapps/common/Half-Life 2/hl2")

    # extract world materials and textures
    materials = copyMaterials(mapData["materials"], gamePath)
    matData = copyTextures(materials, gamePath)
    matSizes = matData["sizes"]

    # extract models, model materials and textures
    copyModels(mapData["models"], gamePath)
    mdlMaterials = copyModelMaterials(mapData["models"], gamePath)
    mdlMatData = copyTextures(mdlMaterials, gamePath, True)

    # create GDT files
    worldMats = createMaterialGdt(matData["vmts"], BO3)
    open(f"{copyDir}/converted/source_data/_corvid_worldmaterials.gdt", "w").write(worldMats["gdt"])
    if not BO3:
        open(f"{copyDir}/converted/bin/_corvid_worldmaterials.bat", "w").write(worldMats["bat"])
    modelMats = createMaterialGdt(mdlMatData["vmts"], BO3)
    open(f"{copyDir}/converted/source_data/_corvid_modelmaterials.gdt", "w").write(modelMats["gdt"])
    if not BO3:
        open(f"{copyDir}/converted/bin/_corvid_modelmaterials.bat", "w").write(modelMats["bat"])
    models = createModelGdt(mapData["models"], BO3)
    open(f"{copyDir}/converted/source_data/_corvid_models.gdt", "w").write(models["gdt"])
    if not BO3:
        open(f"{copyDir}/converted/bin/_corvid_models.bat", "w").write(models["bat"])
    # create GDT files for images for Bo3
    if BO3:
        worldImages = createImageGdt(matData)
        open(f"{copyDir}/converted/source_data/_corvid_worldimages.gdt", "w").write(worldImages)
        modelImages = createImageGdt(mdlMatData)
        open(f"{copyDir}/converted/source_data/_corvid_modelimages.gdt", "w").write(modelImages)

    # convert the textures
    # convertImages(matData, "matTex", "texture_assets/corvid", "tif" if BO3 else "tga")
    # convertImages(mdlMatData, "mdlTex", "texture_assets/corvid", "tif" if BO3 else "tga")

    # convert the models
    # convertModels(mapData["models"], BO3)
    
    # generate map geometry
    mapPatches = ""
    mapBrushes = ""
    mapEnts = ""
    worldSpawnSettings = ""

    table = vertexTable()

    for brush in mapData["worldBrushes"]:
        if not brush.hasDisp:
            mapBrushes += convertBrush(brush)
        for side in brush.sides:
            if side.material.startswith("tools"):
                continue
            if side.hasDisp:
                mapPatches += convertDisplacement(side, matSizes, table)
            if brush.hasDisp:
                continue
            mapPatches += convertSide(side, matSizes, table)

    for brush in mapData["entityBrushes"]:
        if not brush.hasDisp:
            mapBrushes += convertBrush(brush, False)
        for side in brush.sides:
            if side.material.startswith("tools"):
                continue
            if side.hasDisp:
                mapPatches += convertDisplacement(side, matSizes, table)
            if brush.hasDisp:
                continue
            mapPatches += convertSide(side, matSizes, table)

    for entity in mapData["entities"]:
        if entity["classname"].startswith("prop_"):
            mapEnts += convertProp(entity)
        elif entity["classname"] == "light":
            mapEnts += convertLight(entity)
        elif entity["classname"] == "light_spot":
            mapEnts += convertSpotLight(entity, BO3)
        elif entity["classname"] == "move_rope" or entity["classname"] == "keyframe_rope":
            mapEnts += convertRope(entity)
        elif entity["classname"] == "env_cubemap":
            mapEnts += convertCubemap(entity)
        elif entity["classname"].startswith("info_player") or entity["classname"].endswith("_spawn"):
            mapEnts += convertSpawner(entity)
        elif entity["classname"] == "light_environment":
            _color = entity["_ambient"].split(" ")
            color = Vector3(_color[0], _color[1], _color[2]) / 255
            worldSpawnSettings += f' "_color" "{color}"\n'
            _light = entity["_light"].split(" ")
            light = Vector3(_light[0], _light[1], _light[2]) / 255
            worldSpawnSettings += f' "suncolor" "{light}"\n'
            angles = entity["angles"].split(" ")
            pitch = entity["pitch"]
            sundirection = pitch + " " + angles[1] + " " + angles[2]
            worldSpawnSettings += f' "sundirection" "{sundirection}"\n'
    res = ("iwmap 4\n"
           + "{\n"
           + ' "classname" "worldspawn"\n'
           + ' "reflection_ignore_portals" "1"\n'
           + ' "sunlight" "1"\n'
           + ' "sundiffusecolor" "0.75 0.82 0.85"\n'
           + ' "diffusefraction" ".2"\n'
           + ' "ambient" ".116"\n'
           + worldSpawnSettings
           + mapBrushes
           + mapPatches
           + "}\n"
           + mapEnts
           )

    return res