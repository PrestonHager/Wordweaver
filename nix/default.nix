{ pkgs, pythonEnv }:

let
  # Python packages needed for the application
  pythonPackages = ps: with ps; [
    pyqt6
    platformdirs
    pyperclip
    # Note: ipapy is installed via git in pyproject.toml
  ];

  # Create Python environment with packages
  python = pythonEnv.withPackages pythonPackages;

in
pkgs.stdenv.mkDerivation {
  pname = "wordweaver";
  version = builtins.readFile ../VERSION;

  src = pkgs.lib.cleanSource ../.;

  nativeBuildInputs = [
    pkgs.makeWrapper
    python
  ];

  buildInputs = [
    python
  ] ++ pkgs.lib.optionals pkgs.stdenv.isLinux [
    pkgs.xorg.libX11
    pkgs.xorg.libxcb
    pkgs.libGL
    pkgs.fontconfig
    pkgs.freetype
    pkgs.dbus
    pkgs.glib
    pkgs.qt6.full
  ] ++ pkgs.lib.optionals pkgs.stdenv.isDarwin [
    pkgs.darwin.apple_sdk.frameworks.Cocoa
    pkgs.darwin.apple_sdk.frameworks.CoreFoundation
    pkgs.darwin.apple_sdk.frameworks.ApplicationServices
  ];

  installPhase = ''
    mkdir -p $out/bin $out/share/wordweaver

    # Copy source files
    cp -r src/* $out/share/wordweaver/
    cp VERSION $out/share/wordweaver/

    # Create wrapper script
    makeWrapper ${python}/bin/python $out/bin/wordweaver \
      --add-flags "$out/share/wordweaver/main.py" \
      --prefix PYTHONPATH : "$out/share/wordweaver" \
      ${pkgs.lib.optionalString pkgs.stdenv.isLinux ''
        --prefix LD_LIBRARY_PATH : "${pkgs.lib.makeLibraryPath buildInputs}" \
        --set QT_QPA_PLATFORM_PLUGIN_PATH "${pkgs.qt6.qtbase}/lib/qt-6/plugins"
      ''}
  '';

  meta = with pkgs.lib; {
    description = "A complete toolbox for all things conlang";
    homepage = "https://github.com/PrestonHager/Wordweaver";
    license = licenses.mit;
    maintainers = [ ];
    platforms = platforms.unix;
  };
}
