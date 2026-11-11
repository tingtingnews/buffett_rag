from setuptools import setup, find_packages

setup(
    name="buffett-rag",
    version="0.1.0",
    packages=find_packages(),
    py_modules=["cli"],          # tells Python: cli.py is a top-level module
    install_requires=[
        "anthropic",
        "chromadb",
        "sentence-transformers",
        "yfinance",
        "click",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "buffett=cli:cli",   # 'buffett' command → cli.py → cli()
        ],
    },
)
