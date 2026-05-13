from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="erpnext_ai",
    version="0.0.1",
    description="AI Employees & Agent Loop for ERPNext — NocoBase-inspired",
    author="Aries",
    author_email="admin@aries.local",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
