import os
from setuptools import setup


with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# Get install_requires from requirements.txt
with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
    install_requires = f.read().splitlines()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='e89-drf-utils',
    version='0.1.0',
    packages=['drf_utils'],
    include_package_data=True,
    license='MIT License',
    license_files=('LICENSE.txt',),
    description='Utilities for Django Rest Framework.',
    long_description=README,
    url='http://www.estudio89.com.br/',
    author='Luccas Correa',
    author_email='luccascorrea@estudio89.com.br',
    install_requires=install_requires,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.8',
    ],
)