from setuptools import setup


setup(
    name='nionswift_elabftw_plugin',

    version='0.1.2',

    description='A simple plugin to allow users to manage their ElabFTW experiments metadata through Nionswift.',
    long_description='',

    author='Sherjeel Shabih',
    author_email='shabihsherjeel@gmail.com',

    license='GNU General Public License v3.0',
    url='https://github.com/shabihsherjeel/nionswift_elabftw_plugin',
    download_url = 'https://github.com/shabihsherjeel/nionswift_elabftw_plugin/archive/v0.1.2-alpha.tar.gz',
    keywords = ['NIONSWIFT', 'ELABFTW','ELN', 'PLUGIN'],
    packages=['nionswift_plugin.nionswift_elabftw_plugin'],
    install_requires=['elabapy','cryptography', 'nionutils', 'nionui', 'nionswift'],
    classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Science/Research',
    'Programming Language :: Python :: 3',
    ],
    )
