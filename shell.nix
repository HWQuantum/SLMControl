with import <nixpkgs> {};
stdenv.mkDerivation {
                    name = "SLMControl_environment";
                    buildInputs = [
                    (python3.withPackages (ps: with ps; [pyqt5 numpy pyqtgraph ]))
                    ];
}
