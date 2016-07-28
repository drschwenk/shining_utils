import numpy as np
import cv2
import json
import glob
import os
import argparse
import PIL.Image as Image

rect_types = ['text', 'arrowHeads']
poly_types = ['blobs', 'arrows', 'backgroundBlobs']


def load_local_annotation(image_name, annotation_dir):
    file_path = annotation_dir + image_name + '.json'
    with open(file_path, 'r') as f:
        local_annotations = json.load(f)
    return local_annotations


def draw_polygon_on_image(image, polygon, color):
        points = np.int32([polygon])
        cv2.polylines(image, points, color=color, isClosed=True, thickness=2)


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    lv = len(hex_color)
    rgb_color = tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    return rgb_color


def get_category_color(category):
    color_map = {
        "unlabeled": "#8c9296",
        "intraObjectLinkage": "#e7d323",
        "intraObjectTextLinkage": "#e7d323",
        "intraObjectLabel": "#286a8e",
        "interObjectLinkage": "#3fb62c",
        "intraObjectLoop": "#BA70CC",
        "arrowDescriptor": "#e77423",
        'intraObjectRegionLabel': "#696100",
        'sectionTitle': "#ff00ff",
        'imageTitle': "#8256AD",
        'imageCaption': "#ff3300",
        'textMisc': "#cccc00"
    }

    rgb_color = hex_to_rgb(color_map[category])
    rgb_flipped = rgb_color[::-1]
    return rgb_flipped


def build_relationships_to_draw(image_annotations, image_name):

    def flatten_const_dict(image_annotations):
        types_annotated = rect_types + poly_types + ['imageConsts']
        flattened_const_dict = {}
        for anno_type, annotations in image_annotations.items():
            anno_plus_type = {k: v.update({'type': anno_type}) for k, v in annotations.items()}
            if anno_type in types_annotated:
                flattened_const_dict.update(annotations)
        return flattened_const_dict
    
    flattened_const_dict = flatten_const_dict(image_annotations)
    relationships_with_props = {}
    for rel_id, relationship in image_annotations['relationships'].items():
        involved_const_ids = rel_id.split('+')
        rel_category = relationship['category']

        try:
            involved_const = {k: flattened_const_dict[k] for k in involved_const_ids}
        except KeyError as e:
            print image_name
            print e
        relationships_with_props[rel_id] = {
            "rel_id": rel_id,
            "category": rel_category,
            "constituents": involved_const
        }
        
    return relationships_with_props


def visualize_relationships(relationships_to_viz, image_name, output_base_dir, image_dir):
    
    image_result_dir = output_base_dir + image_name.split('.')[0] + '/'
    try:
        os.mkdir(image_result_dir)
    except OSError as e:
        pass
    
    pil_image = Image.open(image_dir + image_name)
    for rel_id, relationship in relationships_to_viz.items():
        open_cv_image = np.array(pil_image) 
        open_cv_image = open_cv_image[:, :, ::-1].copy() 
        rel_category = relationship['category']
        if rel_category == 'arrowHeadTail':
            continue
        for c_id, constituent in relationship['constituents'].items():
            if constituent['type'] in rect_types:
                ul, lr = constituent['rectangle']
                cv2.rectangle(open_cv_image, tuple(ul), tuple(lr), color=get_category_color(rel_category), thickness=2)
            if constituent['type'] in poly_types:
                draw_polygon_on_image(open_cv_image, constituent['polygon'], color=get_category_color(rel_category))
        image_path = image_result_dir + rel_category + '_' + rel_id.replace('+', '_') + '.png'
        cv2.imwrite(image_path, open_cv_image)


def visualize_image_batch(image_dir, annotation_dir, output_dir):
    for image in glob.glob(annotation_dir + '*'):
        image_name = image.split('.json')[0].split('/')[-1]
        image_annotations = load_local_annotation(image_name, annotation_dir)
        to_visualize = build_relationships_to_draw(image_annotations, image_name)
        visualize_relationships(to_visualize, image_name, output_dir, image_dir)


def main():

    parser = argparse.ArgumentParser(description='Writes an image for each relationship in a directory of annotations')
    parser.add_argument('imgdir', help='path to shining diagram images', type=str)
    parser.add_argument('anndir', help='path to directory with annotations', type=str)
    parser.add_argument('outdir', help='directory to write output images', type=str)
    args = parser.parse_args()
    paths = [args.imgdir, args.anndir, args.outdir]
    paths = [path + '/' for path in paths]
    visualize_image_batch(*paths)

if __name__ == "__main__":
    main()
