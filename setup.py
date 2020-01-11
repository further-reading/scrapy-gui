import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="scrapy-GUI",
    version="1.0.3",
    author="Roy Healy",
    author_email="roy.healy87@gmail.com",
    description="A package for offering UI tools for building scrapy queries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/further-reading/scraping-browser",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'requests==2.22.0',
        'PyQtWebEngine-5.14.0',
        'parsel==1.5.2',
        'cssselect==1.1.0',
        'beautifulsoup4==4.8.2',
        'PyQt5==5.14.0',
      ],
    python_requires='>=3.6',
    include_package_data=True,
)
