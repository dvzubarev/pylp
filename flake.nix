{
  description = "Python library for linguistic processing";

  inputs = {
    textapp-pkgs.url = "git+ssh://git@tsa04.isa.ru/textapp/textapp-pkgs?ref=flakes";
    pyexbase.url = "git+ssh://git@tsa04.isa.ru/textapp/pyexbase";

    pyexbase.inputs = {
      textapp-pkgs.follows = "textapp-pkgs";
    };

  };

  outputs = { self,  textapp-pkgs, pyexbase }:
    let pkgs = import textapp-pkgs.inputs.nixpkgs {
          system = "x86_64-linux";
          overlays = [ textapp-pkgs.overlay  self.overlay ];
        };
        python-overlay = pyfinal: pyprev: {pylp = pyfinal.callPackage ./nix {src=self;};};
    in {
      overlay = textapp-pkgs.lib.composeManyExtensions [
        pyexbase.overlay
        (
          final: prev: {python = textapp-pkgs.lib.overridePython python-overlay final prev;}
        )
      ];

      defaultPackage.x86_64-linux = pkgs.python.pkgs.pylp;
      packages.x86_64-linux = {
        inherit (pkgs)
          python;

      };

      devShell.x86_64-linux =
        let pypkgs = pkgs.python.pkgs;
        in
          pkgs.mkShell {
            inputsFrom = [ pypkgs.pylp ];
            buildInputs = [
              textapp-pkgs.packages.x86_64-linux.pyright
              pypkgs.pylint
              pypkgs.black
            ];

            shellHook='' '';
            dontUseSetuptoolsShellHook = true;

          };
    };

}
