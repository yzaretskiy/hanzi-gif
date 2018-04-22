import numpy as np


def coordinate_along_line(x1, y1, x2, y2, t):
    return x1 * (1-t) + x2 * t, y1 * (1-t) + y2 * t


def walker(polyline, step):
    polyline = np.array(polyline)
    lengths = np.linalg.norm(np.diff(polyline, axis=0), axis=1)
    cum_lengths = np.cumsum(lengths)
    current_length = step
    done = False

    yield tuple(polyline[0]), done
    while not done:
        idx = np.searchsorted(cum_lengths, current_length)
        if idx == len(cum_lengths):
            current_length = cum_lengths[-1]
            done = True
            yield tuple(polyline[-1]), done
        else:
            shifted_cum_length = cum_lengths[idx-1] if idx > 0 else 0.0
            t = (current_length - shifted_cum_length) / lengths[idx]
            yield coordinate_along_line(*polyline[idx], *polyline[idx+1], t), done
        current_length += step


def adjust_point_by(points, index, offset):
    points = np.array(points)
    distance = np.linalg.norm(np.diff(points, axis=0))
    new_point = points[index] + (points[1] - points[0]) * offset / distance
    return new_point
