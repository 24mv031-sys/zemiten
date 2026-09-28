"""Build a six-marker stick figure in a TouchDesigner Script SOP.

Expected CHOP: /project1/markers_in
Expected channels: marker1_x .. marker6_x, marker1_y .. marker6_y,
and marker1_found .. marker6_found.
"""


MARKER_CHOP = 'markers_in'
MARKER_COUNT = 6


def _channel_value(chop, name, default=0.0):
    channel = chop[name] if chop is not None else None
    return float(channel[0]) if channel is not None else default


def _read_points():
    chop = op(MARKER_CHOP)
    if chop is None:
        return []

    points = []
    for marker_number in range(1, MARKER_COUNT + 1):
        found = _channel_value(
            chop,
            'marker{}_found'.format(marker_number),
            0.0,
        )
        if found <= 0.5:
            continue

        x = _channel_value(chop, 'marker{}_x'.format(marker_number), -1.0)
        y = _channel_value(chop, 'marker{}_y'.format(marker_number), -1.0)
        if x >= 0.0 and y >= 0.0:
            points.append((x, y))

    return points


def _assign_body_parts(points):
    """Assign six unordered points using their screen positions."""
    if len(points) != MARKER_COUNT:
        return None

    remaining = list(points)

    head = max(remaining, key=lambda point: point[1])
    remaining.remove(head)

    feet = sorted(remaining, key=lambda point: point[1])[:2]
    for foot in feet:
        remaining.remove(foot)

    # Of the three middle points, the lowest one is treated as the torso.
    torso = min(remaining, key=lambda point: point[1])
    remaining.remove(torso)

    hands = sorted(remaining, key=lambda point: point[0])
    feet = sorted(feet, key=lambda point: point[0])

    return {
        'head': head,
        'torso': torso,
        'left_hand': hands[0],
        'right_hand': hands[1],
        'left_foot': feet[0],
        'right_foot': feet[1],
    }


def _to_sop_space(point):
    # Convert normalized image coordinates from 0..1 to SOP coordinates -1..1.
    return (point[0] * 2.0 - 1.0, point[1] * 2.0 - 1.0, 0.0)


def _append_line(script_op, start, end):
    polygon = script_op.appendPoly(2, closed=False, addPoints=True)
    polygon[0].point.P = _to_sop_space(start)
    polygon[1].point.P = _to_sop_space(end)


def _append_joint(script_op, point, radius=0.025):
    # A small diamond makes each detected position visible in the SOP viewer.
    x, y, z = _to_sop_space(point)
    polygon = script_op.appendPoly(4, closed=True, addPoints=True)
    polygon[0].point.P = (x, y + radius, z)
    polygon[1].point.P = (x + radius, y, z)
    polygon[2].point.P = (x, y - radius, z)
    polygon[3].point.P = (x - radius, y, z)


def cook(scriptOP):
    scriptOP.clear()

    body = _assign_body_parts(_read_points())
    if body is None:
        scriptOP.addWarning('Six detected markers are required.')
        return

    connections = (
        ('head', 'torso'),
        ('torso', 'left_hand'),
        ('torso', 'right_hand'),
        ('torso', 'left_foot'),
        ('torso', 'right_foot'),
    )

    for start_name, end_name in connections:
        _append_line(scriptOP, body[start_name], body[end_name])

    for point in body.values():
        _append_joint(scriptOP, point)


def onPulse(par):
    return


def setupParameters(scriptOP):
    return
