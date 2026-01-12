# NixOS overlay for Wordweaver
# To use this overlay in your NixOS configuration:
#
# 1. Copy this file to your NixOS configuration directory
# 2. Add it to your overlays in configuration.nix:
#    nixpkgs.overlays = [ (import ./wordweaver-overlay.nix) ];
# 3. Install with: environment.systemPackages = [ pkgs.wordweaver ];

final: prev: {
  wordweaver = import ./default.nix {
    pkgs = final;
    pythonEnv = final.python312;
  };
}
