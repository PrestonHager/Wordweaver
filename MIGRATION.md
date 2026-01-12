# Transition to uv Package Manager and Nix Flakes

This document explains the transition from pip with requirements.txt to uv package manager with Nix Flakes support.

## What Changed?

### Package Management
- **Before**: Dependencies managed with `requirements.txt` and pip
- **After**: Dependencies managed with `pyproject.toml` and uv package manager
- **Benefit**: Faster installs, better dependency resolution, reproducible builds with `uv.lock`

### Development Environment
- **Before**: Manual Python environment setup
- **After**: Automated Nix Flakes environment with all dependencies
- **Benefit**: Consistent development environment across all platforms, no manual dependency installation

### Domain Name
- **Before**: `xyz.prestonhager.wordweaver`
- **After**: `com.prestonhager.wordweaver`
- **Affected**: macOS bundle identifier, Windows app ID

## Migration Guide for Contributors

### If you were using pip:

**Old workflow:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
python -m unittest discover test
```

**New workflow (Option 1 - using uv):**
```bash
uv sync
uv run python src/main.py
uv run python -m unittest discover test
```

**New workflow (Option 2 - using Nix):**
```bash
nix develop
uv sync
uv run python src/main.py
uv run python -m unittest discover test
```

### If you're on NixOS:

You can now install Wordweaver system-wide using the flake or overlay. See `nix/README.md` for details.

### CI/CD

GitHub Actions workflows have been updated:
- They now use uv for faster dependency installation
- They work on all platforms (Linux, macOS, Windows)
- No changes needed to your PR workflow

## Key Files

### New Files
- `pyproject.toml` - Project metadata and dependencies (replaces requirements.txt)
- `uv.lock` - Locked dependencies for reproducible builds (like poetry.lock or Pipfile.lock)
- `flake.nix` - Nix Flakes configuration for development environment
- `nix/default.nix` - Nix package definition
- `nix/overlay.nix` - NixOS overlay for system-wide installation
- `nix/README.md` - Comprehensive Nix documentation

### Removed Files
- `requirements.txt` - Replaced by pyproject.toml

### Modified Files
- `README.md` - Updated with new setup instructions
- `.github/workflows/python-app.yml` - Updated to use uv
- `.github/workflows/python-app-build.yml` - Updated to use uv
- `.readthedocs.yaml` - Updated to use uv and pyproject.toml
- `.gitignore` - Added uv and Nix-specific entries
- `Wordweaver.spec` - Changed bundle identifier
- `src/main.py` - Changed app ID

## Why These Changes?

### Why uv?
1. **Speed**: 10-100x faster than pip for dependency resolution and installation
2. **Better dependency resolution**: Handles complex dependency trees better
3. **Lock files**: Reproducible builds with uv.lock
4. **Modern**: Uses pyproject.toml standard (PEP 621)
5. **Compatible**: Works with existing pip packages

### Why Nix Flakes?
1. **Reproducibility**: Exact same environment on any machine
2. **Isolation**: No conflicts with system packages
3. **Declarative**: All dependencies declared in one file
4. **Cross-platform**: Works on Linux, macOS, and Windows (via WSL2)
5. **Easy CI/CD**: Can use in GitHub Actions or other CI systems
6. **NixOS integration**: Native package for NixOS users

### Why pyproject.toml?
1. **Standard**: PEP 621 standard for Python projects
2. **All-in-one**: Project metadata, dependencies, and tool configuration in one file
3. **Tool support**: Supported by pip, uv, poetry, hatch, and more
4. **Future-proof**: The future of Python packaging

## Backwards Compatibility

### For end users:
- No changes - installers work the same way
- Application identifier changed (may need to reinstall on macOS)

### For developers:
- Old workflow with pip still works (Option 3 in README)
- Can gradually migrate to uv or Nix
- All tests and builds work the same way

## Getting Help

- **uv documentation**: https://docs.astral.sh/uv/
- **Nix documentation**: https://nixos.org/manual/nix/stable/
- **Nix Flakes guide**: https://nixos.wiki/wiki/Flakes
- **Project setup**: See README.md
- **Nix-specific help**: See nix/README.md

## Troubleshooting

### Issue: `uv: command not found`
**Solution**: Install uv:
```bash
# Unix/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows
irm https://astral.sh/uv/install.ps1 | iex
# Or with pip
pip install uv
```

### Issue: Nix commands don't work
**Solution**: Install Nix and enable flakes:
```bash
# Install Nix
sh <(curl -L https://nixos.org/nix/install)
# Enable flakes
mkdir -p ~/.config/nix
echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf
```

### Issue: Dependencies not found when running tests
**Solution**: Run `uv sync` first to install dependencies

### Issue: Git dependency (ipapy) fails to install
**Solution**: This is normal if GitHub is unreachable. The dependency is cached in uv.lock and will use the cached version.

## Questions?

If you have questions about this transition, please:
1. Check the README.md and nix/README.md documentation
2. Open an issue on GitHub
3. Reach out to the maintainers

Thank you for contributing to Wordweaver!
