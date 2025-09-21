from setuptools import find_packages, setup

setup(
    name="encrypted_model_fields",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "cryptography",
        "Django",
    ],
)
