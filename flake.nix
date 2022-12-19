{
  description = "Python library for linguistic processing";

  inputs = {
    textapp-pkgs.url = "git+ssh://git@tsa04.isa.ru/textapp/textapp-pkgs";
    pyexbase.url = "git+ssh://git@tsa04.isa.ru/textapp/pyexbase";

    pyexbase.inputs = {
      textapp-pkgs.follows = "textapp-pkgs";
    };

  };

  outputs = { self,  textapp-pkgs, pyexbase }:
    let pkgs = import textapp-pkgs.inputs.nixpkgs {
          system = "x86_64-linux";
          overlays = [ textapp-pkgs.overlays.default  self.overlays.default ];
        };
        python-overlay = pyfinal: pyprev: {pylp = pyfinal.callPackage ./nix {src=self;};};
        tlib = textapp-pkgs.lib;
    in {
      overlays.default = tlib.composeManyExtensions [
        pyexbase.overlays.default
        (
          final: prev: tlib.overrideAllPyVersions python-overlay prev
        )
      ];

      packages.x86_64-linux = tlib.allPyVersionsAttrSet {final-pkgs=pkgs;
                                                         default="pylp";};
      devShells.x86_64-linux.default =
        let pypkgs = pkgs.python.pkgs;
        in
          pkgs.mkShell {
            inputsFrom = [ pypkgs.pylp ];
            buildInputs = [
              textapp-pkgs.packages.x86_64-linux.pyright
              pypkgs.pylint
              pypkgs.black
              pypkgs.jupyter_server
            ];

            shellHook=''[ -z "$PS1" ] && export PYTHONPATH=`pwd`:$PYTHONPATH || setuptoolsShellHook'';

          };
    };

}
