from setuptools import setup, find_packages

setup(
    name="aiobservability",
    version="0.1.0",
    description="A model-agnostic, zero-trust AI observability and evaluation SDK.",
    author="AI Observe",
    packages=find_packages(),
    install_requires=[
        "sentence-transformers",
        "numpy"
    ],
    python_requires=">=3.8",
)
