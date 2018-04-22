import re

from matplotlib.path import Path
import numpy as np

from traits.api import (
    HasStrictTraits, ArrayOrNone, Instance, Int, List, Property, String,
    cached_property)

from polyline import adjust_point_by


def svg_parse(path):
    path_re = re.compile(r'([MLHVCSQTAZ])([^MLHVCSQTAZ]+)', re.IGNORECASE)
    float_re = re.compile(r'(?:[\s,]*)([+-]?\d+(?:\.\d+)?)')
    vertices = []
    codes = []
    for cmd, values in path_re.findall(path):
        points = [float(v) for v in float_re.findall(values)]
        points = np.array(points).reshape((len(points) // 2, 2))
        codes.append(cmd)
        vertices.extend(points.tolist())
    return np.array(vertices), codes


class Stroke(HasStrictTraits):
    #: Path vertices; shape => (# of points) x 2
    vertices = ArrayOrNone(shape=(None, 2), dtype=np.float64)

    #: Codes for path vertices
    codes = List(String)

    #: Median vertices; shape => # of points x 2
    medians = ArrayOrNone(shape=(None, 2), dtype=np.float64)

    @classmethod
    def from_hanzi_data(cls, path_data, median_data, median_offset=0):
        vertices, codes = svg_parse(path_data)
        median_data[0] = adjust_point_by(median_data[:2], 0, -median_offset)
        traits = {'vertices': vertices, 'codes': codes, 'medians': median_data}
        return cls(**traits)

    def to_mpl_path(self):
        commands = {'M': (Path.MOVETO,), 'L': (Path.LINETO,),
                    'Q': (Path.CURVE3,) * 2, 'C': (Path.CURVE4,) * 3,
                    'Z': (Path.CLOSEPOLY,)}
        mpl_codes = []
        for code in self.codes:
            mpl_codes.extend(commands[code])

        return Path(self.vertices, mpl_codes)


class Character(HasStrictTraits):
    #: List of all strokes that make up a character
    strokes = List(Instance(Stroke))

    #: Radical strokes
    radical_strokes = List(Int)

    #: Bounding box for the character
    bbox = Property(depends_on=['strokes'])

    @cached_property
    def _get_bbox(self):
        xmin, ymin = np.inf, np.inf
        xmax, ymax = -np.inf, -np.inf
        for stroke in self.strokes:
            c_xmin, c_ymin = np.min(stroke.vertices, axis=0)
            c_xmax, c_ymax = np.max(stroke.vertices, axis=0)
            xmin, ymin = min(xmin, c_xmin), min(ymin, c_ymin)
            xmax, ymax = max(xmax, c_xmax), max(ymax, c_ymax)
        return (xmin, xmax), (ymin, ymax)

    def padded_bbox_from_fraction(self, value):
        x_limits, y_limits = self.bbox
        x_length = x_limits[1] - x_limits[0]
        y_length = y_limits[1] - y_limits[0]
        padding =  value * max(x_length, y_length)
        xlims = x_limits[0] - padding, x_limits[1] + padding
        ylims = y_limits[0] - padding, y_limits[1] + padding
        return xlims, ylims


def from_hanzi_data(data, median_offset=0):
    strokes = [Stroke.from_hanzi_data(path_data, median_data, median_offset)
               for path_data, median_data
               in zip(data['strokes'], data['medians'])]
    char = Character(strokes=strokes)
    char.radical_strokes = data.get('radStrokes', [])
    return char
