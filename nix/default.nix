{
  src,
  buildPythonPackage,
  ujson,
  pyexbase,
  pymorphy2,
  pytest

}:
buildPythonPackage {
  pname = "pylp";
  version = "0.5.2";
  inherit src;

  propagatedBuildInputs=[ujson pyexbase pymorphy2];
  checkInputs=[pytest];
  checkPhase="pytest";
}
