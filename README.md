# 📦 PCK: The Universal Language Runner

> **Stop fighting your environment. Start coding.**
> A zero-config, plug-and-play CLI to create, manage, and run projects in Python, Node.js, and C/C++.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Work_in_Progress-orange)]()

## 💡 The Concept

For beginners, setting up a development environment is often harder than learning to code. `PATH` errors, missing compilers, version conflicts... it's a nightmare.

**PCK** solves this by acting as a smart wrapper. It automatically handles the underlying tools (`uv`, `node`, `zig`, `conan`) in **hermetic environments**. You don't need to install GCC globally or mess with system Python versions. It just works.

## ✨ Features

- **Unified Workflow:** Use the same commands (`create`, `add`, `run`) regardless of the language.
- **Zero Global Dependencies:** Tools are installed locally in the project's `.pck` folder.
- **Modern Stack:**
    - 🐍 **Python:** Powered by `uv` for lightning-fast virtual environments.
    - 🟨 **Node.js:** Auto-downloads portable Node binaries.
    - ⚙️ **C/C++:** Uses **Zig** as a portable C compiler (no need for Visual Studio or GCC installation) & **Conan** for packages.
- **Hermetic Shell:** Activate a shell where all tools are magically in your `PATH`.

## 🚀 Usage

### 1. Create a project
Forget boilerplate code. PCK initializes everything for you.

```bash
pck create -py my-script   # Creates a Python project
pck create -js my-app      # Creates a Node.js project
pck create -c  my-game     # Creates a C project (with portable compiler!)
```

### 2. Manage dependencies
One command to rule them all.

```bash
cd my-script
pck add requests    # Detects Python -> calls 'uv add requests'
```

```bash
cd my-app
pck add axios       # Detects Node -> calls 'npm install axios'
```

### 3. Run instantly
No compilation flags to remember.

```bash
pck run
```
*For C/C++, this automatically downloads Zig, compiles your code, and runs the binary.*

### 4. The Magic Shell 🐚
Need to use specific tools manually? Enter the matrix.

```bash
pck shell
```
This opens a new terminal session where `python`, `node`, `gcc` (aliased to zig), and `make` are available and point to the local project versions.

## 🛠️ Architecture

PCK is written in **Python** and leverages the best modern tools:
- **CLI Framework:** [Typer](https://typer.tiangolo.com/)
- **UI/Formatting:** [Rich](https://github.com/Textualize/rich)
- **Backend Tools:** `uv`, `npm`, `zig`, `conan`

## 🗺️ Roadmap

- [ ] **MVP:** Basic CLI structure with Typer & Rich.
- [ ] **Python Support:** Integration with `uv`.
- [ ] **Node.js Support:** Auto-download of Node binaries.
- [ ] **C/C++ Support:** Integration of Zig as the compiler.
- [ ] **Shell Mode:** Environment variable injection system.

## 📄 License

This project is licensed under the **MIT License**. Feel free to fork, contribute, and learn!
```