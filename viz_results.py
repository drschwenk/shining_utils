import numpy as np
import cv2
import json
import glob
import os
import PIL.Image as Image


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
    return tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def get_category_color(category):
    color_map ={}    
    color_map["unlabeled"] = "#8c9296"
    color_map["IntraObjectLinkage"] = "#e7d323"
    color_map["IntraObjectLabel"] = "#286a8e"
    color_map["InterObjectLinkage"] = "#3fb62c"
    color_map["IntraObjectLoop"] = "#BA70CC"
    color_map["arrowDescriptor"] = "#e77423"
    color_map['intraObjectRegionLabel'] = "#696100"
    color_map['sectionTitle'] = "#ff00ff"
    color_map['imageTitle'] = "#8256AD"
    color_map['imageCaption'] = "#ff3300"
    color_map['textMisc'] = "#cccc00"
    return hex_to_rgb(color_map[category])


def build_relationships_to_draw(image_annotations):

    def flatten_const_dict(image_annotations):
        types_annotated = rect_types + poly_types
        flattened_const_dict = {}
        for anno_type, annotations in image_annotations.items():
            anno_plus_type = {k:v.update({'type': anno_type}) for k, v in annotations.items()}
            if anno_type in types_annotated:
                flattened_const_dict.update(annotations)
        return flattened_const_dict
    
    rect_types = ['text']
    poly_types = ['blobs', 'arrows', 'backgroundBlobs']
    flattened_const_dict = flatten_const_dict(image_annotations)
    
    relationships_with_props = {}
    for rel_id, relationship in image_annotations['relationships'].items():
        involved_const_ids = rel_id.split('+')
        rel_category = relationship['category']
        involved_const = {k:flattened_const_dict[k] for k in involved_const_ids}
        relationships_with_props[rel_id] = {
            "rel_id": rel_id,
            "category": rel_category,
            "constituents": involved_const
        }
        
    return relationships_with_props


def visualize_relationship(relationships_to_viz, image_annotation, output_base_dir, image_dir):
    
    image_result_dir = output_base_dir + image_annotation.split('.')[0] + '/'
    try:
        os.mkdir(image_result_dir)
    except OSError as e:
        pass
    
    pil_image = Image.open(image_dir + image_annotation)
    for rel_id, relationship in relationships_to_viz.items():
        open_cv_image = np.array(pil_image) 
        open_cv_image = open_cv_image[:, :, ::-1].copy() 
        rel_category = relationship['category']
        for c_id, constituent in relationship['constituents'].items():
            if constituent['type'] in rect_types:
                ul, lr =  constituent['rectangle']
                cv2.rectangle(open_cv_image, tuple(ul), tuple(lr), color=get_category_color(rel_category), thickness=2)
            if constituent['type'] in poly_types:
                draw_polygon_on_image(open_cv_image, constituent['polygon'], color = get_category_color(rel_category))
        cv2.imwrite(image_result_dir + rel_id.replace('+', '_') + '.png', open_cv_image)