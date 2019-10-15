with import <nixpkgs> {};
stdenv.mkDerivation {
                    name = "SLMControl_environment";
                    buildInputs = [
			(python3.buildEnv.override {
			  extraLibs = with python3Packages; [ pyqt5 numpy pyqtgraph numba matplotlib ];
			  ignoreCollisions = true;
			})
                    ];
}
