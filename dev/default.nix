let
  pkgs = import <nixpkgs> {};
  stdenv = pkgs.stdenv;

in stdenv.mkDerivation {
  name = "fpesa";

  buildInputs = with pkgs; [
    tmux
    python36
    python36Packages.virtualenv
    nginx
    rabbitmq_server
    nodejs-8_x
  ];
}
