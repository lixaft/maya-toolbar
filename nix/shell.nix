{pkgs ? import <nixpkgs> {}}: let
  py = "311";
in
  pkgs.mkShell {
    packages =
      (with pkgs; [
        pre-commit
        twine
        uv
        pkgs."python${py}"
      ])
      ++ (with pkgs."python${py}Packages"; [
        build
        pyside2
        pyyaml
      ]);

    shellHook = ''
      # Setup the python virtual environment.
      if [[ ! -d .venv ]]; then
        uv venv --python ${pkgs."python${py}"}/bin/python .venv
        uv pip install \
          -e .
      fi
      source .venv/bin/activate

      # Source .env file.
      if [[ -f .env ]]; then
        export $(cat .env | xargs)
      fi
    '';
  }
