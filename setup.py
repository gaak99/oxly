from setuptools import setup, find_packages

setup(
    name='oxit',
    description='oxit - observe/merge diffs in Dropbox file revisions',
    version='0.7.24',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'dropbox',
        'pytz',
        'tzlocal',
    ],
    entry_points='''
        [console_scripts]
        oxit=oxit.scripts.clickit:cli
    ''',
    author='Glenn barry',
    author_email='gaak99@gmail.com',
    url='https://github.com/gaak99/oxit.git',
)
