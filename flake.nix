{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [
            (import ./overlay.nix)
          ];
        };
      in {
        devShells = {
          default = pkgs.mkShell {
            buildInputs = with pkgs; [
              python313
              python313Packages.pyqt6
              python313Packages.platformdirs
              python313Packages.pyperclip

              # custom package from overlay
              python3Packages.ipapy

              # development tools
              python313Packages.sphinx
              python313Packages.pyinstaller
              python313Packages.pylint
            ];
          };
        };
      });
}
