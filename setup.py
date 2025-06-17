import setuptools

setuptools.setup(
    name='doc-converter',
    version='1.3.14',
    author="NEOMO GmbH",
    author_email="magnus.finkenzeller@neomo.com",
    description="A library to convert them all. Get text and metadata from document types like pdf and html.",
    packages=setuptools.find_packages(exclude=["*.tests", "*.tests.*"]),
    python_requires='>=3.6, <4',
    install_requires=[
        'python-poppler==0.3.0',
        'BeautifulSoup4',
        'newspaper3k',
        'regex',
        'lxml==4.9.3'
    ],
    tests_require=['pytest'],
)
