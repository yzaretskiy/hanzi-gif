from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.path import Path
import matplotlib.patches as patches
import numpy as np
from scipy.misc import imresize

from traits.api import HasStrictTraits, Instance, Int, List, Tuple


class MplFrameMaker(HasStrictTraits):
    figure = Instance(Figure)
    frame_dims = Tuple(Int, Int)
    _axes = Instance(Axes)
    _patches = List

    def __axes_default(self):
        ax = self.figure.add_axes([0.0, 0.0, 1.0, 1.0], frameon=False, aspect=1)
        ax.set_xticks([])
        ax.set_yticks([])
        return ax

    def set_xlim(self, xmin, xmax):
        self._axes.set_xlim(xmin, xmax)

    def set_ylim(self, ymin, ymax):
        self._axes.set_ylim(ymin, ymax)

    def add_path(self, path, facecolor='k', edgecolor='k', alpha=None, lw=1,
                 clipping_radius=0, clipping_pt=(0, 0)):
        stroke_patch = patches.PathPatch(
            path, facecolor=facecolor, edgecolor=edgecolor,
            alpha=alpha, lw=lw, antialiased=True
        )
        if clipping_radius > 0:
            circle = Path.circle(clipping_pt, clipping_radius)
            patch = patches.PathPatch(circle, visible=False)
            self._axes.add_patch(patch)
            self._axes.add_patch(stroke_patch).set_clip_path(patch)
        else:
            self._axes.add_patch(stroke_patch)
        self._patches.append(stroke_patch)

    def draw(self):
        canvas = self.figure.canvas
        canvas.draw()
        frame = np.fromstring(canvas.tostring_rgb(), dtype=np.uint8, sep='')
        frame = frame.reshape(canvas.get_width_height()[::-1] + (3,))
        frame = imresize(frame, self.frame_dims)
        return frame

    def clear(self):
        for patch in self._patches:
            patch.remove()
        self._patches = []
