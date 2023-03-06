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
  version = "0.5.6";
  inherit src;

  propagatedBuildInputs=[ujson pyexbase pymorphy2];
  nativeCheckInputs=[pytest];
  checkPhase="pytest";
}
