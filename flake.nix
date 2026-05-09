{
  description = "fridge-gpt development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  };

  outputs = { nixpkgs, ... }:
    let
      systems = [
        "aarch64-darwin"
        "x86_64-darwin"
        "aarch64-linux"
        "x86_64-linux"
      ];

      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          python = pkgs.python312.withPackages (ps: with ps; [
            fastapi
            httpx
            pydantic-settings
            pytest
            uvicorn
          ]);
        in
        {
          default = pkgs.mkShell {
            packages = [
              python
              pkgs.nodejs_22
            ];

            env = {
              FRIDGE_GPT_TOKEN = "dev-token";
              FRIDGE_GPT_DATABASE_URL = "sqlite:///./fridge_gpt.db";
            };

            shellHook = ''
              export PYTHONPATH="$PWD/backend''${PYTHONPATH:+:$PYTHONPATH}"
            '';
          };
        });
    };
}
