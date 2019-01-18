import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(name='dreamnet',
    version='1.1.8',
    description='An adventure game, of sorts, powered by ConceptNet',
    long_description=README,
    long_description_content_type="text/markdown",
    url='http://github.com/EHilly/dreamnet',
    author='Emmet Hilly',
    author_email='emmet.hilly@gmail.com',
    license='MIT',
    packages=['dreamnet'],
    install_requires=[
        'pattern',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'dreamnet = dreamnet.dream:main',
        ]
    },
    include_package_data=True,
    zip_safe=False)