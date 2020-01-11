import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="scrapy-GUI",
    version="1.0.2",
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
    python_requires='>=3.6',
    include_package_data=True,
)
