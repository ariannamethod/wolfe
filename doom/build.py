"""Build the existing WOLFE embedding API as a shared library."""

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wolfe-dir", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    source = args.wolfe_dir.resolve() / "wolfe.c"
    output = Path(__file__).resolve().parent / ".build"
    output.mkdir(exist_ok=True)
    suffix = ".dylib" if platform.system() == "Darwin" else ".so"
    library = output / ("libwolfe" + suffix)
    command = ["cc", "-O2", "-std=c99", "-Wall", "-Wextra", "-Wpedantic", "-fPIC",
               "-DWOLFE_NO_MAIN", "-dynamiclib" if suffix == ".dylib" else "-shared",
               str(source), "-lm", "-o", str(library)]
    subprocess.run(command, check=True)
    revision = subprocess.check_output(["git", "-C", str(args.wolfe_dir), "rev-parse", "HEAD"], text=True).strip()
    metadata = {
        "wolfe_revision": revision,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "library_sha256": hashlib.sha256(library.read_bytes()).hexdigest(),
        "source": str(source), "library": library.name,
        "build_command": command, "platform": platform.platform(),
    }
    (output / "build.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
