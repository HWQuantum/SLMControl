with import <nixpkgs> {};
let hharp = callPackage ./hydraHarpLib.nix {};
    adaptive = callPackage ./adaptive.nix {
      buildPythonPackage = python3Packages.buildPythonPackage;
      fetchPypi = python3Packages.fetchPypi;
      sortedcollections = python3Packages.sortedcollections;
      scipy = python3Packages.scipy;
      atomicwrites = python3Packages.atomicwrites;
      pytest = python3Packages.pytest;
      setuptools = python3Packages.setuptools;
    };
in
stdenv.mkDerivation {
  name = "SLMControl_environment";
  buildInputs = [
    qt5Full
    hharp
    (python3.buildEnv.override {
      extraLibs = with python3Packages; [ pyqt5 numpy pyqtgraph numba matplotlib adaptive ];
      ignoreCollisions = true;
    })
  ];
  LD_LIBRARY_PATH = "${hharp}/lib";
  PYUEYE_DLL_PATH = "/usr/lib/";
}
