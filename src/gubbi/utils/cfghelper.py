##
# cfghelper.py
#
# @author Prahlad Yeri <prahladyeri@yahoo.com>
# @license MIT
import os
import json

def get_config_dir(pkg_name):
    """
    Returns the full path to settings.json for this package.
    Auto creates directories if missing.
    """
    tpath = os.path.expanduser(os.path.join("~", ".config", pkg_name))
    os.makedirs(tpath, exist_ok=True)
    return tpath

def save_settings(pkg_name, cfg):
    """Save the settings dict as json"""
    fname = os.path.join( get_config_dir(pkg_name), 'settings.json')
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4)

def get_settings(pkg_name):
    """Fetch settings for given package from json"""
    cfg = {}
    fname = os.path.join( get_config_dir(pkg_name), 'settings.json')
    if os.path.exists(fname):
        with open(fname, 'r', encoding='utf-8') as f:
            try:
                cfg = json.load(f)
            except:
                return {}
    return cfg