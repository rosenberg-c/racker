def collection_name(
    units,
    thickness_mm,
    depth_mm,
    front_rails,
    back_rails,
    clearance_mm=0.0,
):
    base = (
        f"MU_{_format_mm(units)}U_"
        f"{_format_mm(thickness_mm)}x{_format_mm(depth_mm)}"
        f".c{_format_mm(clearance_mm)}"
    )
    if front_rails and back_rails:
        return f"{base}.front-back"
    if front_rails:
        return f"{base}.front"
    if back_rails:
        return f"{base}.back"
    return base


def _format_mm(value):
    if value is None:
        return "0"
    if abs(value - round(value)) < 1e-6:
        return str(int(round(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def unique_collection_name(base_name, existing_names):
    if base_name not in existing_names:
        return base_name
    index = 2
    while True:
        candidate = f"{base_name}.{index}"
        if candidate not in existing_names:
            return candidate
        index += 1


def total_height_mm(units, top_bottom_z, unit_height):
    return (top_bottom_z * 2.0) + (units * unit_height)


def total_height_from_config(units, config):
    return total_height_mm(units, config.top_bottom_z, config.unit_height)


def rail_length_mm(total_height, top_bottom_z):
    return total_height - (top_bottom_z * 2.0)


def rail_length_from_config(units, config):
    return rail_length_mm(total_height_from_config(units, config), config.top_bottom_z)


def rail_face_y_mm(top_bottom_y, rail_offset_front, rail_offset_back):
    front = -(top_bottom_y * 0.5) + rail_offset_front
    back = (top_bottom_y * 0.5) - rail_offset_back
    return front, back


def rail_face_y_from_config(config, rail_offset_front, rail_offset_back):
    return rail_face_y_mm(config.top_bottom_y, rail_offset_front, rail_offset_back)


def rail_hole_zs_mm(units, top_bottom_z, unit_height, hole_offsets):
    rail_top_z = total_height_mm(units, top_bottom_z, unit_height) - top_bottom_z
    positions = []
    for unit_index in range(units):
        base_z = rail_top_z - (unit_index * unit_height)
        for offset in hole_offsets:
            hole_z = base_z - offset
            if top_bottom_z <= hole_z <= rail_top_z:
                positions.append(hole_z)
    return positions


def faceplate_hole_zs_mm(units, unit_height, hole_offsets):
    top_offset = hole_offsets[0]
    total_height = units * unit_height
    return [total_height - top_offset, top_offset]


def rail_hole_zs_from_config(units, config):
    return rail_hole_zs_mm(units, config.top_bottom_z, config.unit_height, config.hole_offsets)


def rail_x_faces_mm(top_bottom_x, side_x, rail_outset):
    left = -((top_bottom_x * 0.5) - side_x) - rail_outset
    right = ((top_bottom_x * 0.5) - side_x) + rail_outset
    return left, right


def rail_x_faces_from_config(config, rail_outset):
    return rail_x_faces_mm(config.top_bottom_x, config.side_x, rail_outset)
