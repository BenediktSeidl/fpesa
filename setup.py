from setuptools import find_packages, setup

setup(
    name="fpesa",
    version="0.0.2",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pika<0.11',
        'jsonschema',
        'websockets',
        'aio-pika',
        'sqlalchemy',
        'psycopg2',
        'aiohttp',
    ],
    entry_points={
        'console_scripts': [
            'fpesa = fpesa.cli:main',
        ],
    },
)
