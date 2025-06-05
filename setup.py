from setuptools import setup, find_packages
from pathlib import Path

setup(
    name="PikoAi",
    version="0.1.12",
    packages=find_packages(where="Src"),
    py_modules=["cli", "OpenCopilot"],
    package_dir={"": "Src"},
    package_data={
        "Tools": ["tool_dir.json"],
    },
    include_package_data=True,
    install_requires=[
        "python-dotenv>=1.0.1",
        "openai>=1.58.1",
        "groq>=0.22.0",
        "requests>=2.32.3",
        "pdfplumber>=0.11.4",
        "beautifulsoup4>=4.13.4",
        "duckduckgo_search>=7.4.2",
        "rich>=13.9.4",
        "mistralai>=1.2.5",
        "click>=8.1.8",
        "httpx>=0.28.1",
        "psutil>=5.9.8",
        "inquirer>=3.1.3",
        "litellm",
        "PyPDF2",
        "python-docx"
    ],
    entry_points={
        'console_scripts': [
            'piko=cli:cli',
            'pikoai=cli:cli',
        ],
    },
    author="Nihar S",
    author_email="nihar.sr22@gmail.com",
    description="An AI-powered task automation tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/nihaaaar22/OS-Assistant",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 