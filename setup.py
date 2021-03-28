from setuptools import find_packages, setup

setup(
    name="e3-py-tools",
    author="Anders Lindh Olsson",
    python_requires=">=3.6",
    packages=find_packages(),
    setup_requires=["setuptools_scm"],
    entry_points={"scripts": "e3py=e3py.e3py:main"},
)
