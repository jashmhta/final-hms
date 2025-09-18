from setuptools import setup, find_packages
setup(
    name="encrypted_model_fields",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "cryptography",
        "Django",
    ],
)