# 📦 PCK: The Universal Language Runner

> **Stop fighting your environment. Start coding.**
> A zero-config, plug-and-play CLI to create, manage, and run projects in Python, Node.js, and C/C++.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Work_in_Progress-orange)]()

## 💡 The Concept

For beginners, setting up a development environment is often harder than learning to code. `PATH` errors, missing compilers, version conflicts... it's a nightmare.

**PCK** solves this by acting as a smart wrapper. It automatically handles the underlying tools (`uv`, `node`, `zig`, `conan`) in **hermetic environments**. You don't need to install GCC globally or mess with system Python versions. It just works.

## ✨ Features

- **Unified Workflow:** Use the same commands (`create`, `install`, `run`) regardless of the language.
- **Portable Tools:** Tools are installed locally in the PCK installation folder. No global pollution.
- **Modern Stack:**
    - 🐍 **Python:** Powered by `uv` for lightning-fast virtual environments.
    - 🟨 **Node.js:** Auto-downloads portable Node binaries.
    - ⚙️ **C/C++:** Uses **Zig** as a portable C compiler (no need for Visual Studio or GCC installation) & **Conan** for packages.
- **Interactive Shell:** PCK launches as a shell, keeping your context and variables ready.

## 📥 Installation & Startup

No complex installation required. This tool is designed to be portable.

### 1. First Setup
Run this script **only once** to prepare the internal environment.
```bash
setup_env_win.bat
```

### 2. Launch PCK
To start coding, simply run:
```bash
run_win.bat
```
*This opens the **PCK Shell**, ready for your commands.*

## 🚀 Usage

Once inside the PCK Shell, you can navigate your folders and use the `pck` commands.

### 1. Create a project (In-Place or New Folder)
PCK works where you are.

```bash
# In the current directory
pck create -py 3.11    # Sets up Python 3.11 environment here
pck create -c          # Creates a main.c here

# Or create a new folder
pck create -js my-app  # Creates 'my-app' folder with Node.js init
```

### 2. Manage dependencies
One command to rule them all. PCK detects the environment context.

```bash
pck install requests    # Detects Python -> calls 'uv pip install requests'
pck install figlet      # Detects Node -> calls 'npm install figlet'
pck install fmt/10.2.1  # Detects C/C++ -> calls 'conan install ...'
```

### 3. Run instantly
No compilation flags to remember. PCK detects `main.py`, `index.js`, or `main.c`.

```bash
pck run
```
*For C/C++, this automatically downloads Zig, compiles your code to an .exe, and runs it.*

## 🛠️ Architecture

PCK is written in **Python** and leverages the best modern tools:
- **CLI Framework:** [Typer](https://typer.tiangolo.com/)
- **UI/Formatting:** [Rich](https://github.com/Textualize/rich)
- **Backend Tools:** `uv`, `npm`, `zig`, `conan`

## 🗺️ Roadmap

- [x] **MVP:** Basic CLI structure with Typer & Rich.
- [x] **Python Support:** Integration with `uv`.
- [x] **Node.js Support:** Auto-download of Node binaries.
- [x] **C/C++ Support:** Integration of Zig as the compiler.
- [ ] **Linux Support:** Adapt paths and binaries for Linux.
- [ ] **Zig Lang Support:** Support for `.zig` files.
- [x] **Folder Management:** Improve clean-up and organization.
- [x] **Advanced C++:** Automatic linking between Conan packages and Zig compiler.

## ❤️ Acknowledgements

This project stands on the shoulders of giants. It wouldn't exist without these incredible open-source technologies that make modern development possible:

- **[uv](https://github.com/astral-sh/uv):** An extremely fast Python package installer and resolver.
- **[Zig](https://ziglang.org/):** A general-purpose programming language and toolchain for maintaining robust, optimal, and reusable software.
- **[Conan](https://conan.io/):** The C/C++ Package Manager.
- **[Node.js](https://nodejs.org/):** The JavaScript runtime built on Chrome's V8 JavaScript engine.

## 📄 License

This project is licensed under the **MIT License**. Feel free to fork, contribute, and learn!