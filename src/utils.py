import yaml
import os

# On récupère le chemin absolu du dossier parent de ce fichier (src/ -> pck/)
# __file__ est le chemin de utils.py
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_config():
    config_path = os.path.join(ROOT_DIR, "config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # On force le chemin absolu pour le dossier 'langage' dans la config chargée
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