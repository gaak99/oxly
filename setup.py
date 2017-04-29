from setuptools import setup, find_packages

setup(
    name='oxly',
    description='oxly - merge diffs in Emacs/Dropbox/Orgzly file revisions',
    version='0.10.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'dropbox>=7.2.1',
        'pytz',
        'tzlocal',
        'pickledb',
    ],
    entry_points='''
        [console_scripts]
        oxly=oxly.scripts.clickit:cli
    ''',
    author='Glenn barry',
    author_email='gaak99@gmail.com',
    url='https://github.com/gaak99/oxly.git',
)
