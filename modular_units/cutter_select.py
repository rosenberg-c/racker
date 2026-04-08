def _original_obj(obj):
    original = getattr(obj, "original", None)
    return original if original is not None else obj


def original_name(obj) -> str:
    original = _original_obj(obj)
    return getattr(original, "name", obj.name)


def matches_prefix(obj, prefix: str = "MU_") -> bool:
    return original_name(obj).startswith(prefix)


def matches_cutter_piece(obj, prefix: str = "MU_") -> bool:
    name = original_name(obj)
    if not name.startswith(prefix):
        return False
    return not name.startswith("MU_Rail")


def matches_instance_root(inst, root_obj) -> bool:
    root_original = _original_obj(root_obj)

    instance_object = getattr(inst, "instance_object", None)
    if instance_object is not None:
        instance_original = _original_obj(instance_object)
        if instance_original == root_original:
            return True

    parent = getattr(inst, "parent", None)
    while parent is not None:
        parent_original = _original_obj(parent)
        if parent_original == root_original:
            return True
        parent = getattr(parent, "parent", None)

    return False
