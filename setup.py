from setuptools import setup, find_packages
import os

source_dir = 'source'

packages = find_packages(os.path.join('.', source_dir))
package_dir = {}
for package in packages:
    package_path = os.path.join(*package.split('.'))
    package_dir[package] = os.path.join(source_dir, package_path)

install_requires = []
dependency_links = []

setup(
    name='pytesting',
    version='0.0.1',
    packages=packages,
    package_dir=package_dir,
    include_package_data=True,
    install_requires=install_requires,
    dependency_links=dependency_links,
)
