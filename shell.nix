{ pkgs ? import <textapp-pkgs> {},
  latest ? import <nixpkgs> {} }:
with pkgs;
let pythonEnv = python.withPackages (ps: [
      ps.pylint
      ps.pytest
      ps.black
      ps.pyexbase
      ps.ujson
      ps.pymorphy2
    ]);
in
mkShell {
  name = "pylp-dev";
  buildInputs = [
    latest.nodePackages.pyright
    pythonEnv
  ];
  shellHook=''PYTHONPATH=`pwd`:"$PYTHONPATH"'';
}
