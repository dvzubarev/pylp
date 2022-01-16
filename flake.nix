{
  description = "Python library for linguistic processing";

  inputs.textapp-pkgs.url = "git+ssh://git@ids/textapp/textapp-pkgs?ref=flakes";
  inputs.nixpkgs.follows = "textapp-pkgs/nixpkgs";
  inputs.pyexbase.url = "git+ssh://git@ids/textapp/pyexbase";

  outputs = { self, nixpkgs, textapp-pkgs, pyexbase }:
    let pkgs = import nixpkgs {
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
