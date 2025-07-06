import setuptools

# Yes, the README is very important. This code reads your README.md file
# to use as the long description for your package on the PyPI website.
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    # Core metadata for your package
    # TODO: Fill in your project's details here
    name="meta_ai_api",
    author="Masab Saleem",
    author_email="saleemmasab@gmail.com",
    description="A Python wrapper to interact with the Meta AI API",
    keywords=["llm", "ai", "meta", "meta-ai", "api-wrapper"],
    long_description=long_description,
    long_description_content_type="text/markdown",

    # These two lines are essential for projects with a 'src' layout.
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),

    # Classifiers help users find your package on PyPI.
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],

    # This is a critical field that prevents installation on unsupported Python versions.
    python_requires=">=3.6",

    # These are the core packages your project needs to run.
    install_requires=[
        "requests",
        "requests-html",
        "lxml_html_clean"
    ],

    # 'extras_require' is for optional dependencies, like for development.
    extras_require={
        "dev": ["check-manifest"],
    },
)
