from setuptools import setup, find_packages

setup(
    name="taskmanager",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "aiogram>=3.0.0",
        "sqlalchemy>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
) 