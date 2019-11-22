from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()

setup(name='pyonf',
      version='0.2',
      description='Easy configuration from command line or YAML file',
      long_description=readme(),
      long_description_content_type="text/markdown",
      url='http://github.com/simfu/pyonf',
      author='simfu',
      author_email='simfu@free.fr',
      license='GPL',
      keywords='configuration option argparse yaml command line argument',
      packages=['pyonf'],
      install_requires=['pyyaml'],
      include_package_data=True,
      zip_safe=False)
