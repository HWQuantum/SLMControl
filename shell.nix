with import <nixpkgs> {};
let hharp = callPackage ./hydraHarpLib.nix {};
in
stdenv.mkDerivation {
  name = "SLMControl_environment";
  buildInputs = [
    hharp
    (python3.buildEnv.override {
      extraLibs = with python3Packages; [ pyqt5 numpy pyqtgraph numba matplotlib ];
      ignoreCollisions = true;
    })
  ];
  LD_LIBRARY_PATH = "${hharp}/lib";
}
