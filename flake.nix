{
  description = "Wordweaver - A complete toolbox for all things conlang";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };
        
        # Python with uv
        pythonEnv = pkgs.python312;
        
        # Development shell dependencies
        buildInputs = [
          pythonEnv
          pkgs.uv
          pkgs.git
        ];
        
        # Additional dependencies for different platforms
        linuxDeps = pkgs.lib.optionals pkgs.stdenv.isLinux [
          pkgs.xorg.libX11
          pkgs.xorg.libxcb
          pkgs.libGL
          pkgs.fontconfig
          pkgs.freetype
          pkgs.dbus
          pkgs.qt6.qtbase
          pkgs.qt6.qtdeclarative
          pkgs.qt6.wrapQtAppsHook
          pkgs.python3Packages.pyqt6
          pkgs.stdenv.cc.cc
          pkgs.libxkbcommon
          pkgs.glib
          pkgs.gsettings-desktop-schemas
          pkgs.gtk3
          pkgs.libz
          pkgs.zstd
        ];
        
        # Linux shell hook with GSettings setup (what wrapGAppsHook3 does)
        linuxShellHook = pkgs.lib.optionalString pkgs.stdenv.isLinux ''
          export QT_QPA_PLATFORM_PLUGIN_PATH="${pkgs.qt6.qtbase}/lib/qt-6/plugins"
          export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath linuxDeps}:$LD_LIBRARY_PATH"
          # Set up GSettings schemas - construct path like wrapGAppsHook3 does
          export XDG_DATA_DIRS="${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}:${pkgs.glib}/share/gsettings-schemas/${pkgs.glib.name}:${pkgs.gtk3}/share/gsettings-schemas/${pkgs.gtk3.name}:$XDG_DATA_DIRS"
        '';
        
        macosDeps = pkgs.lib.optionals pkgs.stdenv.isDarwin [
          pkgs.darwin.apple_sdk.frameworks.Cocoa
          pkgs.darwin.apple_sdk.frameworks.CoreFoundation
          pkgs.darwin.apple_sdk.frameworks.ApplicationServices
        ];
      in
      {
        # Development shell
        devShells.default = pkgs.mkShell {
          nativeBuildInputs = pkgs.lib.optionals pkgs.stdenv.isLinux [
            pkgs.wrapGAppsHook3
          ];
          buildInputs = buildInputs ++ linuxDeps ++ macosDeps;
          
          shellHook = ''
            echo "Wordweaver development environment"
            echo "Python version: $(python --version)"
            echo "uv version: $(uv --version)"
            echo ""
            echo "To install dependencies, run: uv sync"
            echo "To run tests: uv run python -m unittest discover test"
            echo "To run the app: uv run python src/main.py"
            echo ""
            
            # Set environment variables for Qt on Linux
            ${linuxShellHook}
          '';
        };

        # Package definition
        packages.default = import ./nix/default.nix {
          inherit pkgs pythonEnv;
        };

        # Overlay for NixOS systems
        overlays.default = final: prev: {
          wordweaver = self.packages.${system}.default;
        };
      }
    );
}
