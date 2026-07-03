from gubbi import __version__, PKG_NAME
from pathlib import Path
from setuptools import setup, find_packages

HERE = Path(__file__).parent

setup(
    name=PKG_NAME,
    version=__version__,
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