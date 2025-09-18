import sys
this_python = sys.version_info[:2]
min_version = (3, 9)
if this_python < min_version:
    message_parts = [
        "This script does not work on Python {}.{}.".format(*this_python),
        "The minimum supported Python version is {}.{}.".format(*min_version),
        "Please use https://bootstrap.pypa.io/pip/{}.{}/get-pip.py instead.".format(*this_python),
    ]
    print("ERROR: " + " ".join(message_parts))
    sys.exit(1)
import os.path
import pkgutil
import shutil
import tempfile
import argparse
import importlib
from base64 import b85decode
def include_setuptools(args):
    cli = not args.no_setuptools
    env = not os.environ.get("PIP_NO_SETUPTOOLS")
    absent = not importlib.util.find_spec("setuptools")
    python_lt_3_12 = this_python < (3, 12)
    return cli and env and absent and python_lt_3_12
def include_wheel(args):
    cli = not args.no_wheel
    env = not os.environ.get("PIP_NO_WHEEL")
    absent = not importlib.util.find_spec("wheel")
    python_lt_3_12 = this_python < (3, 12)
    return cli and env and absent and python_lt_3_12
def determine_pip_install_arguments():
    pre_parser = argparse.ArgumentParser()
    pre_parser.add_argument("--no-setuptools", action="store_true")
    pre_parser.add_argument("--no-wheel", action="store_true")
    pre, args = pre_parser.parse_known_args()
    args.append("pip")
    if include_setuptools(pre):
        args.append("setuptools")
    if include_wheel(pre):
        args.append("wheel")
    return ["install", "--upgrade", "--force-reinstall"] + args
def monkeypatch_for_cert(tmpdir):
    from pip._internal.commands.install import InstallCommand
    cert_path = os.path.join(tmpdir, "cacert.pem")
    with open(cert_path, "wb") as cert:
        cert.write(pkgutil.get_data("pip._vendor.certifi", "cacert.pem"))
    install_parse_args = InstallCommand.parse_args
    def cert_parse_args(self, args):
        if not self.parser.get_default_values().cert:
            self.parser.defaults["cert"] = cert_path  
        return install_parse_args(self, args)
    InstallCommand.parse_args = cert_parse_args
def bootstrap(tmpdir):
    monkeypatch_for_cert(tmpdir)
    from pip._internal.cli.main import main as pip_entry_point
    args = determine_pip_install_arguments()
    sys.exit(pip_entry_point(args))
def main():
    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp()
        pip_zip = os.path.join(tmpdir, "pip.zip")
        with open(pip_zip, "wb") as fp:
            fp.write(b85decode(DATA.replace(b"\n", b"")))
        sys.path.insert(0, pip_zip)
        bootstrap(tmpdir=tmpdir)
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)
DATA = b
if __name__ == "__main__":
    main()