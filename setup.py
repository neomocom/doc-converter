import setuptools

setuptools.setup(
    name='doc-converter',
    version='1.1',
    author="NEOMO GmbH",
    author_email="magnus.finkenzeller@neomo.com",
    description="A library to convert them all. Get text and metadata from document types like pdf and html.",
    packages=setuptools.find_packages(exclude=["*.tests", "*.tests.*"]),
    python_requires='>=3.6, <4',
    install_requires=[
        'python-poppler',
        'BeautifulSoup4',
        'scispacy==0.4.0',
        'https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.4.0/en_ner_bc5cdr_md-0.4.0.tar.gz'
    ],
    tests_require=['pytest'],
)