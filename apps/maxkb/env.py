import os


def get_env(name, default=None):
    if name.startswith('MAXKB_'):
        jb_name = 'JB_' + name[len('MAXKB_'):]
        return os.getenv(jb_name, os.getenv(name, default))
    return os.getenv(name, default)


def has_env(name):
    if name.startswith('MAXKB_'):
        jb_name = 'JB_' + name[len('MAXKB_'):]
        return jb_name in os.environ or name in os.environ
    return name in os.environ
