{ lib, buildPythonPackage, fetchPypi, sortedcollections, scipy, atomicwrites, pytest, setuptools }:

buildPythonPackage rec {
  pname = "adaptive";
  version = "0.9.0";

  buildInputs = [ pytest ];
  propagatedBuildInputs = [ sortedcollections scipy atomicwrites setuptools ];

  src = fetchPypi {
    inherit pname version;
    sha256 = "941c0815528f93c8a031a2498923c046ee5d8541d928b79255593d22980c6573";
  };

  doCheck = false;

  meta = with lib; {
    homepage = "https://github.com/python-adaptive/adaptive";
    description = "Tools for adaptive parallel sampling of mathematical functions";
    license = licenses.bsd3;
  };
}
