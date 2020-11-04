from functools import partial


def generate_menu(menu, labels, func):
    for label in labels:
        if label != '_':
            action_with_arg = partial(func, label)
            menu.add_command(label=label, command=action_with_arg)
        else:
            menu.add_separator()
