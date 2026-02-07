import argparse
import pathlib

from enzyme_miner.cli import run_from_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Enzyme substrate/kinetics mining pipeline")
    parser.add_argument(
        "--config",
        required=True,
        type=pathlib.Path,
        help="Path to YAML config file.",
    )
    args = parser.parse_args()
    run_from_config(args.config)


if __name__ == "__main__":
    main()
