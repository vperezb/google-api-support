from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="google-api-support",
    version="0.0.14",
    author="Víctor Pérez Berruezo",
    author_email="victor.perez.berruezo@gmail.com",
    description="In this package you will find functions to deal with google apis. Sheets, Drive, Storage and Slides",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vperezb/google-api-support",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Public Domain",
        "Development Status :: 3 - Alpha",
    ],
    install_requires = [
        "google-api-python-client",
        "httplib2",
        "oauth2client",
        "pandas",
        "google-cloud-storage",
    ],
)
