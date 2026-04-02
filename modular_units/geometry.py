def collection_name(units, front_rails, back_rails):
    if front_rails and back_rails:
        return f"MU_{units}.front-back"
    if front_rails:
        return f"MU_{units}.front"
    if back_rails:
        return f"MU_{units}.back"
    return f"MU_{units}"


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


def rail_length_mm(total_height, top_bottom_z):
    return total_height - (top_bottom_z * 2.0)


def rail_face_y_mm(top_bottom_y, rail_offset_front, rail_offset_back):
    front = -(top_bottom_y * 0.5) + rail_offset_front
    back = (top_bottom_y * 0.5) - rail_offset_back
    return front, back


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


def rail_x_faces_mm(top_bottom_x, side_x, rail_outset):
    left = -((top_bottom_x * 0.5) - side_x) - rail_outset
    right = ((top_bottom_x * 0.5) - side_x) + rail_outset
    return left, right
