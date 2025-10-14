# Nix Flakes Setup

This project includes Nix Flakes support for a reproducible development environment and package builds.

## Prerequisites

- [Nix](https://nixos.org/download.html) with flakes enabled

To enable flakes, add the following to your `~/.config/nix/nix.conf` or `/etc/nix/nix.conf`:

```
experimental-features = nix-command flakes
```

## Development Shell

To enter a development environment with all dependencies installed:

```bash
nix develop
```

This will:
- Install Python 3.12
- Install uv package manager
- Install system dependencies (Qt6, graphics libraries, etc.)
- Set up environment variables for Qt on Linux

Once in the shell, install Python dependencies:

```bash
uv sync
```

## Building the Package

To build the Wordweaver package with Nix:

```bash
nix build
```

The built package will be available in the `result/` directory.

## Running the Application

After building with Nix:

```bash
./result/bin/wordweaver
```

Or directly run without building:

```bash
nix run
```

## Using on NixOS

### As a NixOS Package

To use Wordweaver in your NixOS configuration:

1. Add this repository as a flake input in your `flake.nix`:

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    wordweaver.url = "github:PrestonHager/Wordweaver";
  };

  outputs = { self, nixpkgs, wordweaver, ... }: {
    nixosConfigurations.yourHostname = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        ({ pkgs, ... }: {
          nixpkgs.overlays = [ wordweaver.overlays.default ];
          environment.systemPackages = [ pkgs.wordweaver ];
        })
      ];
    };
  };
}
```

2. Rebuild your system:

```bash
sudo nixos-rebuild switch
```

### Using the Overlay

Alternatively, you can use the overlay directly in your configuration.nix:

```nix
{ config, pkgs, ... }:

{
  nixpkgs.overlays = [
    (import /path/to/wordweaver/nix/overlay.nix)
  ];

  environment.systemPackages = with pkgs; [
    wordweaver
  ];
}
```

## Platform Support

The Nix flake is configured to work on:
- **Linux** (x86_64-linux, aarch64-linux)
- **macOS** (x86_64-darwin, aarch64-darwin)
- **Windows** (via WSL2 with NixOS)

Platform-specific dependencies are automatically handled by the flake.

## CI/CD Integration

The GitHub Actions workflows have been updated to use uv for dependency management, which works alongside the Nix setup:

- **Test workflow**: Runs on pull requests
- **Build workflow**: Creates executables for Linux, macOS, and Windows

## Development Tips

### Updating Dependencies

To update Python dependencies:

```bash
uv sync
```

To update Nix dependencies:

```bash
nix flake update
```

### IDE Integration

If using an IDE with Nix support (e.g., VSCode with nix-env-selector):
1. Open the project
2. Run `nix develop` or let your IDE do it automatically
3. Your IDE will have access to all development tools

### Troubleshooting

**Issue**: Qt applications won't start on Linux  
**Solution**: Make sure you're in the Nix shell which sets up the Qt plugin path

**Issue**: Import errors when running tests  
**Solution**: Make sure dependencies are installed with `uv sync`

**Issue**: Nix build fails  
**Solution**: Try `nix flake update` to update dependencies

## Documentation

For more information about:
- Nix Flakes: https://nixos.wiki/wiki/Flakes
- uv package manager: https://docs.astral.sh/uv/
- Project development: See [README.md](../README.md)
