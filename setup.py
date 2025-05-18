from setuptools import setup, find_packages

setup(
    name="taskautomator",
    version="0.1.0",
    packages=find_packages(where="Src"),
    package_dir={"": "Src"},
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
        "psutil>=5.9.8"
    ],
    entry_points={
        'console_scripts': [
            'ocp=cli:cli',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="An AI-powered task automation tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/taskautomator",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 