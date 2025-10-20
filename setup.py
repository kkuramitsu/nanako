#!/usr/bin/env python3
"""Setup script for Nanako programming language."""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "An educational programming language for the generative AI era"

setup(
    name="nanako",
    version="0.1.3",
    author="Nanako Project",
    author_email="",
    description="An educational programming language for the generative AI era",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/kkuramitsu/nanako",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Education",
        "Topic :: Software Development :: Interpreters",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies required
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "nanako=nanako.run_nanako:main",
        ],
    },
    include_package_data=True,
    package_data={
        "nanako": ["../examples/*.nanako", "../data.csv"],
    },
    keywords="educational programming-language japanese interpreter",
    project_urls={
        "Source": "https://github.com/kkuramitsu/nanako",
    },
)

'''
vim setup.py
rm -rf dist/
python3 -m build
#python3 setup.py sdist bdist_wheel
twine upload --repository pypi dist/*
'''