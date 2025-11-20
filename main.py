import typer
import os
import subprocess
import sys
import shlex
from rich.console import Console
from rich.panel import Panel
from src.download import ensure_tool_installed
from src.utils import load_config, get_tool_path, get_npm_command

app = typer.Typer(help="PCK: The Universal Language Runner", add_completion=False)
console = Console()

# --- CHARGEMENT CONFIG ---
try:
    config = load_config()
except Exception as e:
    console.print(f"[bold red]Critical Error loading config:[/bold red] {e}")
    sys.exit(1)

PCK_MAIN_SCRIPT = os.path.abspath(__file__)

def run_command(cmd_list, cwd=None):
    try:
        cmd_list = [str(c) for c in cmd_list]
        process = subprocess.run(cmd_list, cwd=cwd, shell=False)
        return process.returncode
    except Exception as e:
        console.print(f"[bold red]Execution Error:[/bold red] {e}")
        return 1

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
    console.print("[bold cyan]PCK version 0.0.3[/bold cyan]")

# --- CORRECTION ICI ---
@app.command()
def create(
    name: str = typer.Argument(".", help="Project name OR Python version (e.g. 3.11). Default: current dir."),
    # On définit explicitement les drapeaux pour accepter le tiret unique
    py: bool = typer.Option(False, "-py", "--py", help="Create Python project"),
    js: bool = typer.Option(False, "-js", "--js", help="Create Node.js project"),
    c: bool = typer.Option(False, "-c", help="Create C project"),
    cpp: bool = typer.Option(False, "-cpp", "--cpp", "-c++", help="Create C++ project"),
):
    """Initialize environment. Supports -py 3.11 to install in current dir."""
    
    cwd = os.getcwd()
    target_dir = cwd
    version_arg = None

    # Logique de détection Nom vs Version
    if name[0].isdigit():
        version_arg = name
        target_dir = cwd
    elif name == ".":
        target_dir = cwd
    else:
        target_dir = os.path.join(cwd, name)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

    if py:
        uv_path = ensure_tool_installed("uv", config)
        console.print(f"[green]Creating Python environment in {target_dir}...[/green]")
        cmd = [uv_path, "venv", ".venv"]
        if version_arg:
            cmd.extend(["-p", version_arg])
        run_command(cmd, cwd=target_dir)

    elif js:
        node_path = ensure_tool_installed("node", config)
        npm_cmd = get_npm_command(config)
        console.print(f"[green]Initializing Node.js in {target_dir}...[/green]")
        run_command(npm_cmd + ["init", "-y"], cwd=target_dir)

    elif c or cpp:
        ensure_tool_installed("zig", config)
        conan_path = ensure_tool_installed("conan", config)
        ext = "c" if c else "cpp"
        
        console.print(f"[green]Initializing {ext.upper()} environment in {target_dir}...[/green]")
        run_command([conan_path, "profile", "detect", "--force"])

        main_file = os.path.join(target_dir, f"main.{ext}")
        if not os.path.exists(main_file):
            with open(main_file, "w") as f:
                if c:
                    f.write('#include <stdio.h>\n\nint main() {\n    printf("Hello from PCK C!\\n");\n    return 0;\n}')
                else:
                    f.write('#include <iostream>\n\nint main() {\n    std::cout << "Hello from PCK C++!" << std::endl;\n    return 0;\n}')
            console.print(f"[blue]Created basic main.{ext}[/blue]")
    else:
        console.print("[red]Please specify a language flag (-py, -js, -c, -cpp)[/red]")

@app.command()
def install(package: str):
    cwd = os.getcwd()
    files = os.listdir(cwd)
    
    if "package.json" in files:
        ensure_tool_installed("node", config)
        npm_cmd = get_npm_command(config)
        console.print(f"[green]Installing {package} via npm...[/green]")
        run_command(npm_cmd + ["install", package])
        
    elif "pyproject.toml" in files or ".venv" in files or any(f.endswith(".py") for f in files):
        uv_path = ensure_tool_installed("uv", config)
        console.print(f"[blue]Installing {package} via uv...[/blue]")
        run_command([uv_path, "pip", "install", package])
        
    elif any(f.endswith(('.c', '.cpp')) for f in files) or "conanfile.txt" in files:
        conan_path = ensure_tool_installed("conan", config)
        console.print(f"[orange3]Installing {package} via Conan...[/orange3]")
        run_command([conan_path, "install", "--requires", package, "--build=missing", "-g", "CMakeDeps"])
    else:
        console.print("[red]Could not detect environment to install package.[/red]")

@app.command()
def run(script: str = typer.Argument(None, help="Script file")):
    cwd = os.getcwd()
    
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

    if script.endswith(".py"):
        uv_path = ensure_tool_installed("uv", config)
        run_command([uv_path, "run", script])
        
    elif script.endswith(".js"):
        ensure_tool_installed("node", config)
        node_path = get_tool_path("node", config)
        run_command([node_path, script])
        
    elif script.endswith(".c"):
        zig_path = ensure_tool_installed("zig", config)
        exe_name = script.rsplit('.', 1)[0] + ".exe"
        console.print(f"[orange3]Compiling {script}...[/orange3]")
        ret = run_command([zig_path, "cc", script, "-o", exe_name])
        if ret == 0:
            console.print(f"[green]Running {exe_name}...[/green]")
            run_command([os.path.join(cwd, exe_name)])
            
    elif script.endswith(".cpp"):
        zig_path = ensure_tool_installed("zig", config)
        exe_name = script.rsplit('.', 1)[0] + ".exe"
        console.print(f"[orange3]Compiling {script}...[/orange3]")
        ret = run_command([zig_path, "c++", script, "-o", exe_name])
        if ret == 0:
            console.print(f"[green]Running {exe_name}...[/green]")
            run_command([os.path.join(cwd, exe_name)])
    else:
        console.print(f"[red]Unknown file type: {script}[/red]")

if __name__ == "__main__":
    app()