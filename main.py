import os
import argparse
from os import scandir
import xml.etree.ElementTree as ET
from uuid import uuid1
import json
from random import randint


class Converter:
    TAGS_LIST = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

    def __init__(self, path_to_dataset_annotations='', output_dir=''):
        self.annotations = path_to_dataset_annotations
        self.output_dir = output_dir

    def process(self):
        with open('sample_vott.json') as sv:
            vott_data = json.load(sv)
            vott_data['assets'] = {}
            vott_data['tags'] = []
            for tag in Converter.TAGS_LIST:
                vott_data["tags"].append(
                    {
                        "name": tag,
                        "color": self.htmlcolor(randint(40, 200), randint(40, 200), randint(40, 200))
                    }
                )
            for idx, entry in enumerate(scandir(self.annotations)):
                if entry.name.endswith(".xml"):
                    print(entry.name)
                    asset_data = self.read_data_from_xml(entry.path)
                    if idx == 0:
                        vott_data['lastVisitedAssetId'] = asset_data['asset']['id']
                    vott_data['assets'][asset_data['asset']['id']] = asset_data['asset']
                    filename = f"{asset_data['asset']['id']}-asset.json"
                    print(filename)
                    with open(os.path.join(self.output_dir, filename), "w") as ov:
                        json.dump(asset_data, ov, indent=4, sort_keys=True)
            with open(os.path.join(self.output_dir, "output_vott.vott"), "w") as ov:
                json.dump(vott_data, ov, indent=4, sort_keys=True)

    def read_data_from_xml(self, path_to_xml):
        results = {}
        tree = ET.parse(path_to_xml)
        root = tree.getroot()
        xml_attr = {}
        xml_attr['path'] = root.find('path').text
        xml_attr['size'] = root.find('size')
        results['asset'] = {}
        results['asset']['format'] = xml_attr['path'].split('.')[-1]
        results['asset']['id'] = str(uuid1()).replace("-", "")
        results['asset']['name'] = xml_attr['path'].split(os.sep)[-1]
        results['asset']['path'] = "file:" + xml_attr['path'].replace("\\", "/")
        results['asset']['size'] = {
            "width": int(xml_attr['size'].find('width').text),
            "height": int(xml_attr['size'].find('height').text)
        }
        results['asset']['state'] = 2
        results['asset']['type'] = 1
        results['regions'] = []
        for object in root.findall('object'):
            temp_region = {}
            temp_region['id'] = str(uuid1()).replace("-", "")
            temp_region['type'] = "RECTANGLE"
            temp_region['tags'] = list(object.find('name').text)
            obj_bnd_box = object.find('bndbox')
            xmin = int(obj_bnd_box.find('xmin').text)
            ymin = int(obj_bnd_box.find('ymin').text)
            xmax = int(obj_bnd_box.find('xmax').text)
            ymax = int(obj_bnd_box.find('ymax').text)

            temp_region["boundingBox"] = {
                "height": ymax - ymin,
                "width": xmax - xmin,
                "left": ymin,
                "top": ymin
            }
            temp_region['points'] = [
                {
                    "x": xmin,
                    "y": ymin
                },
                {
                    "x": xmax,
                    "y": ymin
                },
                {
                    "x": xmax,
                    "y": ymax
                },
                {
                    "x": xmin,
                    "y": ymax
                }
            ]

            results['regions'].append(temp_region)
        results['version'] = "2.1.0"
        return results

    def htmlcolor(self, r, g, b):
        def _chkarg(a):
            if isinstance(a, int):  # clamp to range 0--255
                if a < 0:
                    a = 0
                elif a > 255:
                    a = 255
            elif isinstance(a, float):  # clamp to range 0.0--1.0 and convert to integer 0--255
                if a < 0.0:
                    a = 0
                elif a > 1.0:
                    a = 255
                else:
                    a = int(round(a * 255))
            else:
                raise ValueError('Arguments must be integers or floats.')
            return a

        r = _chkarg(r)
        g = _chkarg(g)
        b = _chkarg(b)
        return '#{:02x}{:02x}{:02x}'.format(r, g, b)


parser = argparse.ArgumentParser()
parser.add_argument("--anno_path", type=str)
parser.add_argument("--out_dir", type=str)
args = parser.parse_args()

converter = Converter(path_to_dataset_annotations=args.anno_path,
                      output_dir=args.out_dir)
converter.process()
