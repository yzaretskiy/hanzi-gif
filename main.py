import argparse
import json
import os.path as op

import imageio
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
import numpy as np

from draw import MplFrameMaker
from hanzi import from_hanzi_data
from polyline import walker

HANZI_DATA_FOLDER = 'data'


def stroke_data_to_gif(filename, data, output_size=300, fps=30,
                       brush_radius=60, brush_step=30,
                       stroke_color='k', radical_color='orange'):

    frame_maker = MplFrameMaker(figure=plt.figure(figsize=(10, 10)),
                                frame_dims=(output_size, output_size))
    character = from_hanzi_data(data, median_offset=brush_radius)
    xlims, ylims = character.padded_bbox_from_fraction(0.05)
    frame_maker.set_xlim(*xlims)
    frame_maker.set_ylim(*ylims)

    frames = []
    # Add 1 second of filled character
    for idx, stroke in enumerate(character.strokes):
        path = stroke.to_mpl_path()
        color = radical_color if idx in character.radical_strokes else stroke_color
        frame_maker.add_path(path, color, color)
    complete_char = frame_maker.draw()
    frames.extend([complete_char] * fps)
    frame_maker.clear()

    # Then 1 second of the transparent character
    for idx, stroke in enumerate(character.strokes):
        path = stroke.to_mpl_path()
        color = radical_color if idx in character.radical_strokes else stroke_color
        color = np.array(mcolors.to_rgb(color))
        color = color + (1.0 - color) * 0.75
        frame_maker.add_path(path, color, color)
    transp_char = frame_maker.draw()
    frames.extend([transp_char] * fps)

    # draw over the transparent character
    for idx, stroke in enumerate(character.strokes):
        path = stroke.to_mpl_path()
        color = radical_color if idx in character.radical_strokes else stroke_color

        w = walker(stroke.medians, step=brush_step)
        for pt, isDone in w:
            # ensure we cover the whole stroke
            radius = brush_radius if not isDone else 200
            frame_maker.add_path(path, color, color,
                                 clipping_radius=radius, clipping_pt=pt)
            frames.append(frame_maker.draw())

    imageio.mimwrite(filename, frames, format='gif', fps=fps, subrectangles=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-c', '--character', type=str, required=True)
    ap.add_argument('-s', '--size', type=int, required=True)
    args = ap.parse_args()

    char = args.character
    filepath = op.join(HANZI_DATA_FOLDER, '{}.json'.format(char))
    if op.exists(filepath):
        with open(filepath) as fp:
            data = json.loads(fp.read())
        stroke_data_to_gif('{}-order.gif'.format(char), data, args.size)
    else:
        print("No data available for {}".format(char))


if __name__ == '__main__':
    main()
