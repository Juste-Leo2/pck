import os
import zipfile
import requests
import shutil
from rich.console import Console
from rich.progress import Progress

console = Console()

def ensure_tool_installed(tool_name: str, config: dict):
    base_dir = config['settings']['base_dir']
    tool_conf = config['tools'][tool_name]
    
    tool_dir = os.path.join(base_dir, tool_conf['folder_name'])
    
    # Full path to the target executable
    exe_full_path = os.path.join(base_dir, tool_conf['exe_path'])

    if os.path.exists(exe_full_path):
        return exe_full_path

    console.print(f"[bold yellow]📦 Tool '{tool_name}' not found. Installing into {tool_dir}...[/bold yellow]")
    
    # Create the specific folder if it does not exist
    os.makedirs(tool_dir, exist_ok=True)

    url = tool_conf['url']
    zip_path = os.path.join(base_dir, f"{tool_name}_temp.zip")
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_length = int(r.headers.get('content-length', 0))
            
            with Progress() as progress:
                task = progress.add_task(f"[green]Downloading {tool_name}...", total=total_length)
                with open(zip_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))

        console.print(f"[blue]Extracting {tool_name}...[/blue]")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract EVERYTHING to the specific folder for the tool.
            zip_ref.extractall(tool_dir)
            

    except Exception as e:
        console.print(f"[bold red]Error installing {tool_name}: {e}[/bold red]")
        if os.path.exists(tool_dir):
            shutil.rmtree(tool_dir, ignore_errors=True)
        return None
    
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)

    # Final verification
    if os.path.exists(exe_full_path):
        console.print(f"[bold green]✅ {tool_name} installed successfully![/bold green]")
        return exe_full_path
    else:
        console.print(f"[bold red]❌ Installation seems to have failed. File not found: {exe_full_path}[/bold red]")
        # Debug: List files to understand structure
        # console.print(f"Content of {tool_dir}: {os.listdir(tool_dir)}")
        return None