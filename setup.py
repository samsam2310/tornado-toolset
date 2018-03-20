from setuptools import setup, find_packages


setup(
    name='tornado-toolset',
    version='0.1.1',
    author='Sam Wu',
    author_email='samsam2310@gmail.com',
    packages=find_packages(),
    install_requires=[],
    extras_require={
        'dev': [
            'yapf',
        ],
    }, )
