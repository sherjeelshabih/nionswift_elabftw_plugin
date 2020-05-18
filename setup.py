from setuptools import setup


setup(
    name='nionswift_elabftw_plugin',

    version='0.1',

    description='A simple plugin to allow users to manage their ElabFTW experiments metadata through Nionswift.',
    long_description='',

    author='Sherjeel Shabih',
    author_email='shabihsherjeel@gmail.com',

    license='GNU General Public License v3.0',
    url='https://github.com/shabihsherjeel/nionswift_elabftw_plugin',
    keywords = ['NIONSWIFT', 'ELABFTW','ELN', 'PLUGIN'],
    packages=['nionswift_plugin.nionswift_elabftw_plugin'],
    install_requires=['elabapy','cryptography', 'nionutils', 'nionui', 'nionswift'],
    classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Researchers',
    'Programming Language :: Python :: 3',
    ],
    )
