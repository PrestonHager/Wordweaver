# overlay file to add a custom nix python package to the python3Packages

self: super: let
  version = "0.0.10.0";
  ipapyOverride = {
    packageOverrides = python-self: python-super: {
      ipapy = python-super.buildPythonPackage {
        pname = "ipapy";
        version = version;
        doCheck = false;
        src = super.fetchFromGitHub {
          owner = "PrestonHager";
          repo = "ipapy";
          rev = "v${version}";
          sha256 = "sha256-dz7bm67S2hPIadChLMNVqQlDSW6V7ESADg8AW9TQng0=";
        };
      };
    };
  };
in rec {
  python = super.python.override ipapyOverride;
  pythonPackages = python.pkgs;
  python3 = super.python3.override ipapyOverride;
  python3Packages = python3.pkgs;
}
