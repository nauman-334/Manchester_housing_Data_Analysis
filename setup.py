from typing import List

from setuptools import find_packages, setup

# Special line in requirements.txt that tells pip to install THIS project
# in editable mode; it is not a library, so setup() must not receive it.
HYPHEN_E_DOT = "-e ."


def get_requirements(file_path: str) -> List[str]:
    """Return the list of libraries listed in a requirements file.

    Blank lines, comments and the "-e ." line are ignored.
    """
    requirements = []
    # Open the file whose name was passed in (the variable, not the text
    # 'file_path' - that was the cause of the FileNotFoundError).
    with open(file_path, encoding="utf-8") as file_obj:
        for line in file_obj:
            # Remove spaces and the line break at the end of the line.
            requirement = line.strip()
            # Skip empty lines, comments and the editable-install marker.
            if not requirement or requirement.startswith("#"):
                continue
            if requirement == HYPHEN_E_DOT:
                continue
            requirements.append(requirement)
    return requirements


setup(
    name="Manchester_housing_Data_Analysis",
    # Version of YOUR project (not the Python version); start at 0.0.1.
    version="0.0.1",
    author="Nauman",
    author_email="legendofcs1@gmail.com",
    packages=find_packages(),
    install_requires=get_requirements("requirements.txt"),
)
