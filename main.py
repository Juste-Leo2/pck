import typer
import os
import subprocess
import sys
import shlex
from importlib.metadata import version as get_version
from rich.console import Console
from rich.panel import Panel
from src.download import ensure_tool_installed
from src.utils import load_config, get_tool_path, get_npm_command
from src import cpp_manager

app = typer.Typer(help="PCK: The Universal Language Runner", add_completion=False)
console = Console()

# --- CONFIG ---
try:
    config = load_config()
except Exception as e:
    console.print(f"[bold red]Critical Error loading config:[/bold red] {e}")
    sys.exit(1)

PCK_MAIN_SCRIPT = os.path.abspath(__file__)

def run_command(cmd_list, cwd=None):
    """Executes a system command (mainly used for Py and JS here)."""
    try:
        # Convert all arguments to string just in case
        cmd_list = [str(c) for c in cmd_list]
        process = subprocess.run(cmd_list, cwd=cwd, shell=False)
        return process.returncode
    except Exception as e:
        console.print(f"[bold red]Execution Error:[/bold red] {e}")
        return 1

def get_python_executable(cwd):
    """
    Detects if a .venv exists in the given directory.
    Returns the path to the python executable inside .venv if it exists,
    otherwise returns None.
    """
    venv_path = os.path.join(cwd, ".venv")
    if os.path.exists(venv_path):
        if os.name == 'nt':  # Windows
            python_exe = os.path.join(venv_path, "Scripts", "python.exe")
        else:  # Unix/Linux/Mac
            python_exe = os.path.join(venv_path, "bin", "python")
        
        if os.path.exists(python_exe):
            return python_exe
    return None

def interactive_shell():
    console.print(Panel("[bold cyan]🐚 PCK Shell Active[/bold cyan]\nType 'exit' to quit.", expand=False))
    while True:
        try:
            cwd = os.getcwd()
            user_input = console.input(f"[bold yellow]{cwd}[/bold yellow] [bold cyan]pck>[/bold cyan] ").strip()
            if not user_input: continue
            if user_input.lower() in ["exit", "quit"]:
                console.print("[cyan]Goodbye![/cyan]")
                break
            
            if user_input.lower().startswith("cd "):
                path = user_input[3:].strip().replace('"', '')
                try: os.chdir(path)
                except Exception as e: console.print(f"[red]Error: {e}[/red]")
                continue
            
            if user_input.lower() in ["cls", "clear"]:
                os.system('cls' if os.name == 'nt' else 'clear')
                continue

            if user_input.lower().startswith("pck "):
                args = shlex.split(user_input[4:])
                
                if getattr(sys, 'frozen', False):
                    subprocess.run([sys.executable] + args)
                else:
                    subprocess.run([sys.executable, PCK_MAIN_SCRIPT] + args)
                continue

            subprocess.run(user_input, shell=True)
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[bold red]Shell Error:[/bold red] {e}")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        interactive_shell()

@app.command()
def version():
    try:
        ver = get_version("pck")
    except:
        ver = "0.0.0"
    console.print(f"[bold cyan]PCK version {ver}[/bold cyan]")

@app.command()
def create(
    name: str = typer.Argument(".", help="Project name (creates a folder). Default: current dir."),
    py: str = typer.Option(None, "-py", "--py", help="Create Python project with version (e.g. -py 3.11)"),
    js: bool = typer.Option(False, "-js", "--js", help="Create Node.js project"),
    c: bool = typer.Option(False, "-c", help="Create C project"),
    cpp: bool = typer.Option(False, "-cpp", "--cpp", "-c++", help="Create C++ project"),
):
    """
    Initialize environment. 
    Example: 'pck create -py 3.11 test' creates a folder 'test' with a Python 3.11 environment.
    """
    
    cwd = os.getcwd()
    
    # Define target directory
    if name == ".":
        target_dir = cwd
    else:
        target_dir = os.path.join(cwd, name)
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
                console.print(f"[green]Created directory: {target_dir}[/green]")
            except OSError as e:
                console.print(f"[red]Error creating directory: {e}[/red]")
                return

    # --- PYTHON ---
    if py is not None:
        # Note: 'py' contains the version string (e.g., "3.11") or "default" if user handled differently
        uv_path = ensure_tool_installed("uv", config)
        console.print(f"[green]Creating Python environment in {target_dir}...[/green]")
        
        cmd = [uv_path, "venv", ".venv"]
        # If the user provided a specific version like "3.11", add it
        if py and py.lower() != "true": 
            cmd.extend(["--python", py])
            
        run_command(cmd, cwd=target_dir)

    # --- NODE.JS ---
    elif js:
        ensure_tool_installed("node", config)
        npm_cmd = get_npm_command(config)
        console.print(f"[green]Initializing Node.js in {target_dir}...[/green]")
        run_command(npm_cmd + ["init", "-y"], cwd=target_dir)

    # --- C / C++ ---
    elif c or cpp:
        lang = "cpp" if cpp else "c"
        console.print(f"[green]Initializing {lang.upper()} environment in {target_dir}...[/green]")
        cpp_manager.create_project(config, target_dir, lang=lang)

    else:
        console.print("[red]Please specify a language flag (-py [ver], -js, -c, -cpp)[/red]")

@app.command()
def install(package: str):
    cwd = os.getcwd()
    files = os.listdir(cwd)
    
    # --- NODE.JS ---
    if "package.json" in files:
        ensure_tool_installed("node", config)
        npm_cmd = get_npm_command(config)
        console.print(f"[green]Installing {package} via npm...[/green]")
        run_command(npm_cmd + ["install", package])
        
    # --- PYTHON ---
    elif "pyproject.toml" in files or ".venv" in files or any(f.endswith(".py") for f in files):
        uv_path = ensure_tool_installed("uv", config)
        console.print(f"[blue]Installing {package} via uv...[/blue]")
        
        # Check if we have a local environment to target specifically
        local_python = get_python_executable(cwd)
        
        if local_python:
            # Target the specific environment python
            run_command([uv_path, "pip", "install", "--python", local_python, package])
        else:
            # Fallback to general install (might install in user scope or temp venv)
            run_command([uv_path, "pip", "install", package])
        
    # --- C / C++ ---
    # Detection: source files, conanfile, or the store folder
    elif any(f.endswith(('.c', '.cpp')) for f in files) or "conanfile.txt" in files or os.path.exists(".conan_store"):
        # Delegation to the C++ manager
        cpp_manager.install_package(config, package)

    else:
        console.print("[red]Could not detect environment to install package.[/red]")

@app.command()
def run(script: str = typer.Argument(None, help="Script file")):
    cwd = os.getcwd()
    
    # Auto-detection of the script if not provided
    if not script:
        files = os.listdir(cwd)
        priority = ["main.py", "app.py", "index.js", "app.js", "main.c", "main.cpp"]
        for p in priority:
            if p in files:
                script = p
                break
        if not script:
            console.print("[red]No script specified.[/red]")
            return

    # --- PYTHON ---
    if script.endswith(".py"):
        # 1. Check for local .venv
        local_python = get_python_executable(cwd)
        
        if local_python:
            # Run using the local environment directly
            console.print(f"[dim]Using local environment: {local_python}[/dim]")
            run_command([local_python, script])
        else:
            # 2. Fallback to uv run (ephemeral or managed environment)
            console.print("[dim]No local .venv found, using uv run...[/dim]")
            uv_path = ensure_tool_installed("uv", config)
            run_command([uv_path, "run", script])
        
    # --- NODE.JS ---
    elif script.endswith(".js"):
        ensure_tool_installed("node", config)
        node_path = get_tool_path("node", config)
        run_command([node_path, script])
        
    # --- C / C++ ---
    elif script.endswith(".c") or script.endswith(".cpp"):
        cpp_manager.run_script(config, script)
        
    else:
        console.print(f"[red]Unknown file type: {script}[/red]")

if __name__ == "__main__":
    app()