import yaml
import os
import sys

def get_root_dir():
    """
    Détermine le dossier racine selon si on est en mode script ou en mode exécutable compilé (Frozen).
    """
    if getattr(sys, 'frozen', False):
        # Cas 1 : On est un .EXE (PyInstaller)
        # On retourne le dossier où se trouve le .exe
        return os.path.dirname(sys.executable)
    else:
        # Cas 2 : On est en développement (script python normal)
        # On retourne le dossier parent de src/
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROOT_DIR = get_root_dir()

def load_config():
    config_path = os.path.join(ROOT_DIR, "config.yaml")
    
    if not os.path.exists(config_path) and getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            internal_path = os.path.join(sys._MEIPASS, "config.yaml")
            if os.path.exists(internal_path):
                config_path = internal_path

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    base_setting = config['settings']['base_dir']
    if not os.path.isabs(base_setting):
        config['settings']['base_dir'] = os.path.join(ROOT_DIR, base_setting)
        
    return config

def get_tool_path(tool_name: str, config: dict):
    base_dir = config['settings']['base_dir']
    exe_rel_path = config['tools'][tool_name]['exe_path']
    return os.path.join(base_dir, exe_rel_path)

def get_npm_command(config: dict):
    node_path = get_tool_path('node', config)
    base_dir = config['settings']['base_dir']
    npm_script = os.path.join(base_dir, config['tools']['node']['npm_path'])
    return [node_path, npm_script]