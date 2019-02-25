from setuptools import setup, find_packages

setup(name='hypotonic',
      version='0.0.2',
      description='Fast asynchronous web scraper with minimalist API.',
      classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Text Processing :: Markup :: HTML'
      ],
      url='https://github.com/mscavnicky/hypotonic',
      author='Martin Scavnicky',
      author_email='martin.scavnicky@gmail.com',
      license='MIT',
      packages=find_packages(exclude=['.semaphore', 'cassettes', 'tests', 'tests.*']),
      install_requires=['aiohttp', 'lxml', 'cssselect'],
      include_package_data=True,
      zip_safe=False)