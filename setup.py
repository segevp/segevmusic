import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="segevmusic",
    version="2.0",
    author="Segev Pavin",
    author_email="macsegev@gmail.com",
    description="Downloading with Deezer and tagging with Apple Music",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/segevp/music-downloader",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Topic :: Multimedia :: Sound/Audio"
    ],
    python_requires='>=3.6',
    install_requires=['deemix>=1.5.8', 'mutagen'],
    entry_points={'console_scripts': ['segevmusic=segevmusic.music_downloader:main']}
)
