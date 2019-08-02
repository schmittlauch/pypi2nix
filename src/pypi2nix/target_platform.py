import os
import platform
import tempfile
from contextlib import contextmanager
from typing import Iterator

from attr import attrib
from attr import attrs

from pypi2nix.nix import Nix
from pypi2nix.utils import PYTHON_VERSIONS


class PlatformGenerator:
    def __init__(self, nix: Nix) -> None:
        self.nix = nix

    def from_python_version(self, version: str) -> "TargetPlatform":
        with self.python_environment_nix(version) as nix_file:
            detected_version = self.nix.shell(
                command='python -c "from platform import python_version; print(python_version())"',
                derivation_path=nix_file,
            ).splitlines()[0]
        return TargetPlatform(
            version=detected_version,
            nixpkgs_derivation_name=self.derivation_from_version_specifier(version),
        )

    @contextmanager
    def python_environment_nix(self, version: str) -> Iterator[str]:
        fd, path = tempfile.mkstemp()
        with open(fd, "w") as f:
            f.write(
                " ".join(
                    [
                        "with import <nixpkgs> {{}};",
                        'stdenv.mkDerivation {{ name = "python3-env"; buildInputs = [{}]; }}',
                    ]
                ).format(self.derivation_from_version_specifier(version))
            )
        yield path
        os.remove(path)

    def derivation_from_version_specifier(self, version: str) -> str:
        return PYTHON_VERSIONS[version]

    def derivation_name_from_python_version(self, version: str) -> str:
        return self.derivation_from_version_specifier(version[:3])

    def current_platform(self) -> "TargetPlatform":
        current_version = platform.python_version()
        return TargetPlatform(
            version=current_version,
            nixpkgs_derivation_name=self.derivation_name_from_python_version(
                current_version
            ),
        )


@attrs
class TargetPlatform:
    version: str = attrib()
    nixpkgs_derivation_name: str = attrib()
