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


def build_relationships(rel_dict, arrows_w_heads):
    new_relationships = {}
    for rel, involved_boxes in rel_dict.items():
        if len(involved_boxes['boxes']) == 3:
            ordered_boxes = sorted(involved_boxes['boxes'], key=lambda x: x[0])
        elif len(involved_boxes['boxes']) == 2:
            ordered_boxes = sorted(involved_boxes['boxes'], key=lambda x: x[1][0], reverse=True)
        elif len(involved_boxes['boxes']) == 1:
            ordered_boxes = involved_boxes['boxes'] + [(2, 'I0')]
        else:
            print ('more than three constituents!')
        rel_id = '+'.join([box[1] for box in ordered_boxes])
        new_relationships[rel_id] = {
            'id': rel_id,
            'category': involved_boxes['category'].replace('I', 'i'),
            'has_directionality': False,
            'origin': ordered_boxes[0][1]
        }
        if len(ordered_boxes) > 1:
            new_relationships[rel_id]['destination'] = ordered_boxes[-1][1]
        if len(ordered_boxes) == 3:
            new_relationships[rel_id]['connector'] = ordered_boxes[1][1]
            new_relationships[rel_id]['has_directionality'] = ordered_boxes[1][1] in arrows_w_heads
            if new_relationships[rel_id]['category'] == 'intraObjectLinkage' and ordered_boxes[0][1]:
                new_relationships[rel_id]['category'] = 'intraObjectTextLinkage'

    return new_relationships


def build_and_write_relationships(page_df, anno_dir, new_anno_dir):
    anno_file_name = pd.unique(page_df['page'])[0] + '.json'
    with open(anno_dir + anno_file_name) as f:
        base_anno = json.load(f)

    arrows_with_direction = build_arrowhead_lookup(base_anno['relationships'])

    rel_dict = build_relationship_dict(page_df)
    rel_to_add = build_relationships(rel_dict, arrows_with_direction)
    append_to_annotations(base_anno, new_anno_dir, anno_file_name, rel_to_add)


def build_arrowhead_lookup(arrow_relationships):
    arrows_w_heads = [rel['origin'] for rel_id, rel in arrow_relationships.items()]
    return arrows_w_heads


def append_to_annotations(base_anno, dest_dir, anno_file, new_annotations):
    base_anno['relationships'].update(new_annotations)

    with open(dest_dir + anno_file, 'w') as f:
        json.dump(base_anno, f, indent=4, sort_keys=True)
