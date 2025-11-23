# 📦 PCK: The Universal Language Runner

> **Stop fighting your environment. Start coding.**
> A zero-config CLI to create, manage, and run projects in Python, Node.js, and C/C++.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Releases](https://img.shields.io/github/v/release/Juste-Leo2/pck)](https://github.com/Juste-Leo2/pck/releases)

## 💡 What is PCK?

PCK is a portable wrapper that standardizes how you interact with programming languages. It automatically handles the underlying tools (`uv`, `node`, `zig`, `conan`) in **hermetic environments**.

*   No global pollution.
*   No version conflicts.
*   One syntax for all languages.

## 📥 Installation

### Option 1: Standalone Executable (Recommended)
No Python or dependencies required. Just download and run.

1.  Download the latest **`pck.exe`** from the **[Releases Page](https://github.com/Juste-Leo2/pck/releases/)**.
2.  Add the file to your system **PATH** to use it from any terminal.

### Option 2: Manual Installation (via Pip)
If you prefer running from source or have Python installed:

```bash
# Clone the repository
git clone https://github.com/Juste-Leo2/pck.git
cd pck

# Install via pip (requires Python 3.8+)
pip install .
```

## 🚀 Usage

Once installed, simply type `pck` to enter the interactive shell, or run commands directly.

### 1. Create a Project
Initialize a clean environment instantly.

```bash
pck create -py 3.11   # Python 3.11 environment
pck create -js        # Node.js project
pck create -c MyProjectFolder        # C project (compiled via Zig), optional creates a folder
```



### 2. Install Dependencies
PCK detects the language context and uses the appropriate package manager (`pip`, `npm`, or `conan`).

```bash
pck install requests      # Python
pck install figlet        # Node.js
pck install fmt/10.2.1    # C++
```

### 3. Run
Forget compilation flags. Just run your code.

```bash
pck run main.py
```

## 🛠️ Powered By

PCK leverages the fastest modern tools under the hood:
*   **[uv](https://github.com/astral-sh/uv)** for Python.
*   **[Zig](https://ziglang.org/)** for C/C++ compilation.
*   **[Conan](https://conan.io/)** for C++ dependency management.

## 📄 License

This project is licensed under the **MIT License**.