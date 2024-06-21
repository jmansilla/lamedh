from setuptools import setup, find_packages

setup(
    name='Lamedh',
    version='0.1',
    url='https://github.com/lamedh.git',
    author='Javier Mansilla',
    author_email='javimansilla@gmail.com',
    description='Lambda Reduction and Evaluation',
    packages=find_packages(),
    scripts=['bin/lamedh'],
    package_data={'': ['help.txt']},
    include_package_data=True,
    install_requires=['lark==1.1.9', 'prompt_toolkit==3.0.47', 'pytest==8.2.2'],
)
