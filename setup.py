from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="orbit_pyqtgraph",
    version="1.0.0",
    author="Islam Trabeih",
    author_email="islamtrabeih@azhar.edu.eg",
    description="A comprehensive orbit visualization toolkit using PyQt5, OpenGL, PIL, and datetime",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Islamtrabeih/orbit_pyqtgraph/tree/main",
    packages=find_packages(),
    package_data={
        'libassets': ['assets/*.jpg', 'assets/*.png'],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Astronomy",
        "Topic :: Scientific/Engineering :: Visualization",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    keywords="orbit, visualization, astronomy, satellite, pyqt5, opengl, pil",
     project_urls={
        "Source": "https://github.com/Islamtrabeih/orbit_pyqtgraph/tree/main",
    },
)
