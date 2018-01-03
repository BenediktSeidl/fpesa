from setuptools import find_packages, setup

setup(
    name="fpesa",
    version="0.0.1",
    packages=find_packages(),
    # TODO: package data! default.conf
    install_requires=[
        'werkzeug',
        'pika<0.11',
        'jsonschema',
        'websockets',
        'aio-pika',
    ],
    entry_points={
        'console_scripts': [
            'fpesa = fpesa.cli:main',
        ],
    },
)
