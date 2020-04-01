from setuptools import setup


setup(
    name='nionswift_elabftw_plugin',

    version='0.1',

    description='',
    long_description='',

    author='Sherjeel Shabih',
    author_email='shabihsherjeel@gmail.com',

    license='GNU General Public License v3.0',

    packages=['nionswift_plugin.nionswift_elabftw_plugin'],
    install_requires=['cryptography', 'elabapy'],
    zip_safe=False,
    )
