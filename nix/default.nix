{
  src,
  buildPythonPackage,
  ujson,
  pyexbase,
  pymorphy2,
  wn,
  pylp-resources,
  pytest

}:
buildPythonPackage {
  pname = "pylp";
  version = "0.5.7";
  inherit src;

  propagatedBuildInputs=[ujson pyexbase pymorphy2 wn
                         pylp-resources];
  nativeCheckInputs=[pytest];
  checkPhase="pytest";
}
