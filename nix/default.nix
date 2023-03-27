{
  src,
  buildPythonPackage,
  ujson,
  pyexbase,
  pymorphy2,
  pylp-resources,
  pytest

}:
buildPythonPackage {
  pname = "pylp";
  version = "0.5.8";
  inherit src;

  propagatedBuildInputs=[ujson pyexbase pymorphy2
                         pylp-resources];
  nativeCheckInputs=[pytest];
  checkPhase="pytest";
}
