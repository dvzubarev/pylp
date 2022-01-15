{
  description = "Python library for linguistic processing";

  inputs.textapp-pkgs.url = "git+ssh://git@ids/textapp/textapp-pkgs?ref=flakes";
  inputs.nixpkgs.follows = "textapp-pkgs/nixpkgs";
  inputs.pyexbase.url = "git+ssh://git@ids/textapp/pyexbase";

  outputs = { self, nixpkgs, textapp-pkgs, pyexbase }:
    let pkgs = import nixpkgs {
          system = "x86_64-linux";
          overlays = [ textapp-pkgs.overlay pyexbase.overlay self.overlay ];
        };
    in {
      overlay = final: prev:
        let merged-overlay = pkgs.lib.composeExtensions
          prev.python-overlay
          (pyfinal: pyprev: {pylp = pyfinal.callPackage ./nix {src=self;};});
        in {
          python-overlay = merged-overlay;
          python = prev.base-python.override{packageOverrides = merged-overlay;};
        };
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
