def get_child_by_name(parent_widget, name):
    for child in parent_widget.get_children():
        if child.get_name() == name:
            print("child", child, "found")
            return child
        
        elif hasattr(child, "get_children"):
            return get_child_by_name(child, name)



