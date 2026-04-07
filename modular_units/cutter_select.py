def original_name(obj) -> str:
    original = getattr(obj, "original", None)
    if original is not None:
        return getattr(original, "name", obj.name)
    return obj.name


def matches_prefix(obj, prefix: str = "MU_") -> bool:
    return original_name(obj).startswith(prefix)


def matches_instance_root(inst, root_obj) -> bool:
    root_original = getattr(root_obj, "original", root_obj)

    instance_object = getattr(inst, "instance_object", None)
    if instance_object is not None:
        instance_original = getattr(instance_object, "original", instance_object)
        if instance_original == root_original:
            return True

    parent = getattr(inst, "parent", None)
    while parent is not None:
        parent_original = getattr(parent, "original", parent)
        if parent_original == root_original:
            return True
        parent = getattr(parent, "parent", None)

    return False
