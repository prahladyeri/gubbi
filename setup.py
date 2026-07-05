#from gubbi import __version__, PKG_NAME
import re
from pathlib import Path
from setuptools import setup, find_packages

version_file = Path(__file__).parent / "src" / "gubbi" / "__init__.py"
version_match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]+)[\'"]', version_file.read_text(), re.M)
version = version_match.group(1)

HERE = Path(__file__).parent

setup(
    name="gubbi",
    version=version,
    description="Minimalist terminal LLM chatbot",
    long_description=(HERE / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Prahlad Yeri",
    license="MIT",
    python_requires=">=3.8",

    packages=find_packages(where="src"),
    package_dir={"": "src"},

    install_requires=[
        "requests>=2.32.3",
        "openai>=1.109,<2",
        "colorama>=0.4.6",
        "keyring>=25.5.0"
    ],

    entry_points={
        "console_scripts": [
            "gubbi=gubbi.cli:main",
        ]
    },

    keywords=[
        "llm",
        "chatbot",
        "terminal",
    ],

    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],

    project_urls={
        "Homepage": "https://github.com/prahladyeri/gubbi",
        "Repository": "https://github.com/prahladyeri/gubbi",
        "Issues": "https://github.com/prahladyeri/gubbi/issues",
    },
)