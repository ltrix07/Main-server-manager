from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="main_server_manager",
    version="0.2.1",
    description="Библиотека, которая используется в дополнении с Checker-Plus для взаимодействия чекера, поставщика "
                "прокси и телеграм бота.",
    author="ltrix07",
    author_email="ltrix02@gmail.com",
    url="https://github.com/ltrix07/Main-server-manager",
    packages=find_packages(),
    install_requires=requirements
)