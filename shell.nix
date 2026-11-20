{ pkgs ? import <nixpkgs> {} }:
  pkgs.mkShell {
    nativeBuildInputs = with pkgs; [ black clang-tools qmk pyright poetry python3Packages.pytest ];
}
