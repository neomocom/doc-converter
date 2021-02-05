import setuptools

setuptools.setup(
    name='doc-converter',
    version='0.1',
    author="Magnus Finkenzeller",
    author_email="magnus.finkenzeller@neomo.com",
    description="A library to convert them all. Get text and metadata from document types like pdf and html.",
    packages=['html2text', 'pdf2text'],
    python_requires='>=3.6, <4',
    install_requires=[
        'python-poppler',
        'BeautifulSoup4'
    ],
    tests_require=['pytest'],
)