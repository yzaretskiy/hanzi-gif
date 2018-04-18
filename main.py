import argparse
import json
import os.path as op
import re

import imageio
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.path import Path
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from scipy.misc import imresize


HANZI_DATA_FOLDER = 'data'


def coordinate_along_line(x1, y1, x2, y2, t):
    return x1 * (1-t) + x2 * t, y1 * (1-t) + y2 * t


def polyline_walker(polyline, step):
    polyline = np.array(polyline)
    lengths = np.linalg.norm(np.diff(polyline, axis=0), axis=1)
    cum_lengths = np.cumsum(lengths)
    current_length = step
    done = False

    yield tuple(polyline[0])
    while not done:
        idx = np.searchsorted(cum_lengths, current_length)
        if idx == len(cum_lengths):
            current_length = cum_lengths[-1]
            yield tuple(polyline[-1])
            done = True
        else:
            shifted_cum_length = cum_lengths[idx-1] if idx > 0 else 0.0
            t = (current_length - shifted_cum_length) / lengths[idx]
            yield coordinate_along_line(*polyline[idx], *polyline[idx+1], t)
        current_length += step


def svg_parse(path):
    commands = {'M': (Path.MOVETO,),   'L': (Path.LINETO,),
                'Q': (Path.CURVE3,)*2, 'C': (Path.CURVE4,)*3,
                'Z': (Path.CLOSEPOLY,)}
    path_re = re.compile(r'([MLHVCSQTAZ])([^MLHVCSQTAZ]+)', re.IGNORECASE)
    float_re = re.compile(r'(?:[\s,]*)([+-]?\d+(?:\.\d+)?)')
    vertices = []
    codes = []
    for cmd, values in path_re.findall(path):
        points = [float(v) for v in float_re.findall(values)]
        points = np.array(points).reshape((len(points) // 2, 2))
        codes.extend(commands[cmd.capitalize()])
        vertices.extend(points.tolist())
    return np.array(vertices), codes


def parse_all_strokes(stroke_data):
    stroke_paths = []
    xmin, ymin = np.inf, np.inf
    xmax, ymax = -np.inf, -np.inf
    for stroke in stroke_data:
        vertices, codes  = svg_parse(stroke)
        stroke_paths.append(Path(vertices, codes))
        c_xmin, c_ymin = np.min(vertices, axis=0)
        c_xmax, c_ymax = np.max(vertices, axis=0)
        xmin, ymin = min(xmin, c_xmin), min(ymin, c_ymin)
        xmax, ymax = max(xmax, c_xmax), max(ymax, c_ymax)
    return stroke_paths, (xmin, xmax), (ymin, ymax)


def stroke_data_to_gif(filename, data, output_size=300, fps=30,
                       brush_radius=55, brush_step=20,
                       stroke_color='k', radical_color='k'):
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], frameon=False, aspect=1)
    ax.set_xticks([])
    ax.set_yticks([])

    stroke_paths, x_limits, y_limits = parse_all_strokes(data['strokes'])
    x_length = x_limits[1] - x_limits[0]
    y_length = y_limits[1] - y_limits[0]
    padding = 0.05 * max(x_length, y_length)
    ax.set_xlim(x_limits[0] - padding, x_limits[1] + padding)
    ax.set_ylim(y_limits[0] - padding, y_limits[1] + padding)

    frames = []
    for idx, (path, median) in enumerate(zip(stroke_paths, data['medians'])):
        if 'radStrokes' in data and idx in data['radStrokes']:
            color = radical_color
        else:
            color = stroke_color

        w = polyline_walker(median, step=brush_step)
        for pt in w:
            circle = Path.circle(pt, brush_radius)
            patch = patches.PathPatch(circle, visible=False)
            ax.add_patch(patch)
            stroke_patch = patches.PathPatch(path.deepcopy(),
                                             facecolor=color,
                                             edgecolor=color, lw=1,
                                             antialiased=True)
            ax.add_patch(stroke_patch).set_clip_path(patch)

            fig.canvas.draw()
            mpl_im = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
            mpl_im = mpl_im.reshape(fig.canvas.get_width_height()[::-1] + (3,))
            mpl_im = imresize(mpl_im, (output_size, output_size))
            frames.append(mpl_im)

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


if __name__ == '__main__':
    main()
