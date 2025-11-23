import os
import subprocess
import sys
import glob
import re
import shlex
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from src.download import ensure_tool_installed

console = Console()

LOCAL_CONAN_DIR = ".conan_store"
DEPS_DIR = "pck_modules"
ZIG_CACHE_DIR = ".zig-cache"
WRAPPERS_DIR = "wrappers"

def to_cmake_path(path):
    """Converts Windows backslashes to forward slashes for CMake/Conan."""
    return path.replace('\\', '/')

def get_conan_env(base_env=None):
    env = base_env if base_env else os.environ.copy()
    cwd = os.getcwd()
    local_home = os.path.join(cwd, LOCAL_CONAN_DIR)
    env["CONAN_HOME"] = local_home
    return env, local_home

# --- .PC FILE PARSER (FIXED) ---
def parse_pc_files(search_dir):
    pc_files = glob.glob(os.path.join(search_dir, "*.pc"))
    if not pc_files:
        return [], []

    compiler_flags = [] 
    linker_flags = []   

    var_regex = re.compile(r'^([a-zA-Z0-9_]+)=(.*)$')
    sub_regex = re.compile(r'\$\{([a-zA-Z0-9_]+)\}')

    for pc_file in pc_files:
        variables = {}
        variables['pcfiledir'] = to_cmake_path(os.path.dirname(os.path.abspath(pc_file)))

        with open(pc_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # 1st pass: Read Variables
        for line in lines:
            line = line.strip()
            match = var_regex.match(line)
            if match:
                key, raw_val = match.groups()
                # IMPORTANT: Clean quotes here
                raw_val = raw_val.strip().strip('"').strip("'")
                
                # Recursive resolution
                while True:
                    sub_match = sub_regex.search(raw_val)
                    if not sub_match: break
                    var_name = sub_match.group(1)
                    if var_name in variables:
                        raw_val = raw_val.replace(f"${{{var_name}}}", variables[var_name])
                    else: break
                variables[key] = to_cmake_path(raw_val)

        # 2nd pass: Extract Cflags and Libs
        for line in lines:
            # Replace variables in the line
            while True:
                sub_match = sub_regex.search(line)
                if not sub_match: break
                var_name = sub_match.group(1)
                if var_name in variables:
                    line = line.replace(f"${{{var_name}}}", variables[var_name])
                else: break 
            
            if line.startswith("Cflags:"):
                content = line[7:].strip()
                # shlex.split handles spaces in paths and removes quotes
                args = shlex.split(content)
                for arg in args:
                    if arg not in compiler_flags: compiler_flags.append(arg)
            
            elif line.startswith("Libs:"):
                content = line[5:].strip()
                args = shlex.split(content)
                for arg in args:
                    if arg not in linker_flags: linker_flags.append(arg)

    return compiler_flags, linker_flags

def create_fake_gcc_wrappers(target_dir, zig_path):
    wrappers_path = os.path.join(target_dir, WRAPPERS_DIR)
    if not os.path.exists(wrappers_path):
        os.makedirs(wrappers_path)

    zig_safe = f'"{zig_path}"'
    python_exe = sys.executable
    
    with open(os.path.join(wrappers_path, "gcc.cmd"), "w") as f:
        f.write(f'@echo off\n{zig_safe} cc -target x86_64-windows-gnu %*\n')
    with open(os.path.join(wrappers_path, "g++.cmd"), "w") as f:
        f.write(f'@echo off\n{zig_safe} c++ -target x86_64-windows-gnu %*\n')
    with open(os.path.join(wrappers_path, "ar.cmd"), "w") as f:
        f.write(f'@echo off\n{zig_safe} ar %*\n')
    with open(os.path.join(wrappers_path, "ranlib.cmd"), "w") as f:
        f.write(f'@echo off\n{zig_safe} ranlib %*\n')

    # SHIM CORRIGÉ POUR LES GUILLEMETS
    shim_code = r'''# -*- coding: utf-8 -*-
import sys, subprocess
zig_exe = sys.argv[1]
original_args = sys.argv[2:]
new_args = [zig_exe, 'rc']
infile = None
outfile = None
i = 0
while i < len(original_args):
    arg = original_args[i]
    
    # --- FIX CRITIQUE ICI ---
    # On nettoie les échappements shell (\") qui font planter le compilateur de ressources Zig
    arg = arg.replace(r'\"', '"') 
    
    if arg == '-D':
        i += 1
        if i < len(original_args):
            val = original_args[i].replace(r'\"', '"') # On nettoie aussi la valeur
            new_args.append('/D' + val)
    elif arg.startswith('-D'): 
        new_args.append('/D' + arg[2:])
    elif arg == '-I':
        i += 1; new_args.append('/I' + original_args[i]) if i < len(original_args) else None
    elif arg.startswith('-I'): new_args.append('/I' + arg[2:])
    elif arg == '-o':
        i += 1; outfile = original_args[i] if i < len(original_args) else None
    elif arg.startswith('-O') or arg == '-O': i += 1 
    elif not arg.startswith('-'):
        if not infile: infile = arg
        else: outfile = arg
    i += 1
if outfile: new_args.append('/fo' + outfile)
if infile: new_args.append(infile)
sys.exit(subprocess.run(new_args).returncode)
'''
    shim_path = os.path.join(wrappers_path, "windres_shim.py")
    with open(shim_path, "w", encoding="utf-8") as f:
        f.write(shim_code)

    with open(os.path.join(wrappers_path, "windres.cmd"), "w") as f:
        f.write(f'@echo off\n"{python_exe}" "{shim_path}" {zig_safe} %*\n')

    return wrappers_path

def ensure_conan_profile(conan_path, env):
    profile_path = os.path.join(env["CONAN_HOME"], "profiles", "default")
    if not os.path.exists(os.path.dirname(profile_path)):
        os.makedirs(os.path.dirname(profile_path))
    if not os.path.exists(profile_path):
        mingw_profile = "[settings]\nos=Windows\narch=x86_64\ncompiler=gcc\ncompiler.version=11\ncompiler.libcxx=libstdc++11\ncompiler.threads=posix\ncompiler.exception=seh\nbuild_type=Release\n"
        with open(profile_path, "w") as f:
            f.write(mingw_profile)

def create_project(config, target_dir, lang="c"):
    ext = "c" if lang == "c" else "cpp"
    main_file = os.path.join(target_dir, f"main.{ext}")
    
    if not os.path.exists(main_file):
        code = ""
        if lang == "cpp":
            code = '#include <iostream>\nint main() { std::cout << "Hello C++!" << std::endl; return 0; }'
        else:
            code = '#include <stdio.h>\nint main() { printf("Hello C!\\n"); return 0; }'
        with open(main_file, "w") as f: f.write(code)
        console.print(f"[blue]Created main.{ext}[/blue]")

    gitignore_path = os.path.join(target_dir, ".gitignore")
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "w") as f:
            f.write(f"{LOCAL_CONAN_DIR}/\n{DEPS_DIR}/\n{ZIG_CACHE_DIR}/\n{WRAPPERS_DIR}/\n*.exe\n*.obj\n*.pdb\n")

def install_package(config, package_name):
    conan_path = ensure_tool_installed("conan", config)
    ensure_tool_installed("cmake", config)
    ensure_tool_installed("ninja", config)
    zig_path = ensure_tool_installed("zig", config)
    
    env, local_home = get_conan_env()
    cwd = os.getcwd()
    wrappers_path = create_fake_gcc_wrappers(cwd, zig_path)

    # PATH Config
    cmake_bin = os.path.dirname(ensure_tool_installed("cmake", config))
    ninja_bin = os.path.dirname(ensure_tool_installed("ninja", config))
    env["PATH"] = f"{wrappers_path}{os.pathsep}{cmake_bin}{os.pathsep}{ninja_bin}{os.pathsep}{env['PATH']}"
    
    # --- FIX PATH SEPARATORS ---
    # Force forward slashes so tools like libtool don't strip backslashes
    env["CC"] = to_cmake_path(os.path.join(wrappers_path, "gcc.cmd"))
    env["CXX"] = to_cmake_path(os.path.join(wrappers_path, "g++.cmd"))
    env["RC"] = to_cmake_path(os.path.join(wrappers_path, "windres.cmd"))
    
    # --- FIX FOR LIBICONV / LEGACY C LIBS ON WINDOWS ---
    # Legacy libs often have coding styles that modern Clang treats as warnings/errors.
    # "-w" disables all warnings, allowing the build to proceed despite them.
    permissive_flags = "-w"
    env["CFLAGS"] = permissive_flags
    env["CXXFLAGS"] = permissive_flags
    
    ensure_conan_profile(conan_path, env)
    
    if os.path.exists("conanfile.txt"):
        try: os.remove("conanfile.txt")
        except: pass

    ar_cmd = to_cmake_path(os.path.join(wrappers_path, "ar.cmd"))
    ranlib_cmd = to_cmake_path(os.path.join(wrappers_path, "ranlib.cmd"))
    extra_vars = '{"CMAKE_AR": "' + ar_cmd + '", "CMAKE_RANLIB": "' + ranlib_cmd + '"}'
    
    cmd = [
        conan_path, "install", 
        "--requires", package_name, 
        "--build=missing", 
        "--deployer=full_deploy", 
        "-g", "PkgConfigDeps", 
        f"--output-folder={DEPS_DIR}",
        "-c", "tools.cmake.cmaketoolchain:generator=Ninja",
        "-c", f"tools.cmake.cmaketoolchain:extra_variables={extra_vars}"
    ]
    
    # --- DYNAMIC DISPLAY ---
    console.print(f"[bold cyan]📦 PCK Package Manager[/bold cyan]")
    install_success = False
    error_log = []

    with Progress(
        SpinnerColumn("dots", style="bold magenta"),
        TextColumn("{task.description}"),
        transient=False 
    ) as progress:
        task_id = progress.add_task(f"Initializing Conan for {package_name}...", total=None)
        
        # Popen to capture output line by line
        process = subprocess.Popen(
            cmd, 
            env=env, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            encoding='utf-8', 
            errors='replace'
        )

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            
            if line:
                clean_line = line.strip()
                error_log.append(clean_line)
                
                if "Downloading" in clean_line:
                    progress.update(task_id, description=f"[blue]⬇️  Downloading dependencies...[/blue]")
                elif "Building" in clean_line:
                    # Try to extract package name
                    try:
                        pkg = clean_line.split("Building")[1].split()[0]
                    except:
                        pkg = "package"
                    progress.update(task_id, description=f"[orange3]🔨 Building {pkg} (This may take a while)...[/orange3]")
                elif "Installing" in clean_line:
                    progress.update(task_id, description=f"[green]📂 Installing files...[/green]")
                elif "ERROR" in clean_line:
                    progress.update(task_id, description=f"[red]💥 Error detected![/red]")

        install_success = (process.poll() == 0)

    if install_success:
        console.print(f"[bold green]✅ {package_name} successfully installed![/bold green]")
        console.print(f"[dim]   Files are in ./{DEPS_DIR}[/dim]")
    else:
        console.print(f"[bold red]❌ Installation failed![/bold red]")
        console.print("[dim]--- Error Log (Last 20 lines) ---[/dim]")
        for l in error_log[-20:]:
            console.print(f"[red]{l}[/red]")

def run_script(config, script_path):
    zig_path = ensure_tool_installed("zig", config)
    
    is_cpp = script_path.lower().endswith(".cpp") or script_path.lower().endswith(".cc")
    compiler_mode = "c++" if is_cpp else "cc"
    
    exe_name = os.path.splitext(script_path)[0] + ".exe"
    cwd = os.getcwd()
    deps_path = os.path.join(cwd, DEPS_DIR)
    
    # Parse dependencies silently
    cflags, libs_flags = parse_pc_files(deps_path)
    
    target_flags = ["-target", "x86_64-windows-gnu"]
    misc_flags = ["-w", "-O2"] if not is_cpp else ["-w", "-O2", "-std=c++17"]

    cmd = [zig_path, compiler_mode, script_path] + misc_flags + target_flags + cflags + libs_flags + ["-o", exe_name]
    
    env = os.environ.copy()
    env["ZIG_GLOBAL_CACHE_DIR"] = os.path.join(cwd, ZIG_CACHE_DIR)
    env["ZIG_LOCAL_CACHE_DIR"] = os.path.join(cwd, ZIG_CACHE_DIR)

    # --- COMPILATION SPINNER ---
    compile_success = False
    error_msg = ""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Compiling {task.description}..."),
        transient=True
    ) as progress:
        progress.add_task(description=script_path, total=None)
        
        ret = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if ret.returncode == 0:
            compile_success = True
        else:
            error_msg = ret.stderr

    if compile_success:
        console.print(f"[bold green]🚀 Executing {exe_name}...[/bold green]")
        
        new_path = env["PATH"]
        if os.path.exists(deps_path):
            for root, dirs, files in os.walk(deps_path):
                if "bin" in dirs:
                    new_path = os.path.join(root, "bin") + os.pathsep + new_path
        env["PATH"] = new_path
        
        try:
            subprocess.run([os.path.join(cwd, exe_name)], env=env)
        except KeyboardInterrupt:
            pass
    else:
        console.print("[bold red]💥 Compilation failed![/bold red]")
        console.print(error_msg)