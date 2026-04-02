import math


def rail_component_centers_mm(
    x_face,
    x_inward,
    y_face,
    y_inward,
    side_z_center,
    config,
    rotation_z=None,
):
    wood_center_x = x_face + (config.rail_wood_width * 0.5 * x_inward)
    rack_center_x = x_face + (config.rail_thickness * 0.5 * x_inward)

    wood_center_y = y_face + (config.rail_thickness * 0.5 * y_inward)
    rack_center_y = y_face + (config.rail_rack_width * 0.5 * y_inward)

    pivot = (x_face, y_face, side_z_center)
    wood_loc = (wood_center_x, wood_center_y, side_z_center)
    rack_loc = (rack_center_x, rack_center_y, side_z_center)

    if rotation_z:
        wood_loc = _rotate_point_z(wood_loc, pivot, rotation_z)
        rack_loc = _rotate_point_z(rack_loc, pivot, rotation_z)

    return wood_loc, rack_loc


def rail_hole_centers_mm(rack_loc, hole_zs):
    return [(rack_loc[0], rack_loc[1], hole_z) for hole_z in hole_zs]


def _rotate_point_z(point, pivot, rotation_z):
    cos_z = math.cos(rotation_z)
    sin_z = math.sin(rotation_z)

    x = point[0] - pivot[0]
    y = point[1] - pivot[1]

    rot_x = (x * cos_z) - (y * sin_z)
    rot_y = (x * sin_z) + (y * cos_z)

    return (rot_x + pivot[0], rot_y + pivot[1], point[2])
