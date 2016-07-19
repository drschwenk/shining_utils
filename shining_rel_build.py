import json
import ast
import pandas as pd
from collections import defaultdict


def build_relationship_dict(results_df):
    results_df['g_list'] = results_df['group_n'].apply(ast.literal_eval)
    relationship_dict = defaultdict(lambda: defaultdict(list))
    _ = results_df.apply(lambda x: append_to_relationship_dict(x, relationship_dict), axis=1)
    return relationship_dict


def append_to_relationship_dict(row, rel_dict):
    for idx, group in enumerate(row['g_list']):
        if group[0] > 0:
            rel_dict[group[0]]['category'] = row['category'][idx]
            rel_dict[group[0]]['boxes'] .append((group[1], row['id']))


def build_relationships(rel_dict):
    new_relationships = {}
    for rel, involved_boxes in rel_dict.items():
        ordered_boxes = sorted(involved_boxes['boxes'], key=lambda x: x[0])
        rel_id = '+'.join([box[1] for box in ordered_boxes])
        new_relationships[rel_id] = {
            'id': rel_id,
            'category': involved_boxes['category'],
            'has_directionality': True,  # Ask about this
            'origin': ordered_boxes[0][1]
        }
        if len(ordered_boxes) > 1:
            new_relationships[rel_id]['destination'] = ordered_boxes[-1][1]
        if len(ordered_boxes) > 2:
            new_relationships[rel_id]['connector'] = ordered_boxes[1][1]
    return new_relationships


def build_and_write_relationships(page_df, anno_dir, new_anno_dir):
    anno_file_name = pd.unique(page_df['page'])[0] + '.json'
    rel_dict = build_relationship_dict(page_df)
    rel_to_add = build_relationships(rel_dict)
    append_to_annotations(anno_dir, new_anno_dir, anno_file_name ,rel_to_add)


def append_to_annotations(base_dir, dest_dir, anno_file, new_annotations):
    with open(base_dir + anno_file) as f:
        base_anno = json.load(f)
        
    base_anno['relationships'] = new_annotations
    
    with open(dest_dir + anno_file, 'w') as f:
        json.dump(base_anno, f)