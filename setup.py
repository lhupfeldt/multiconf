import sys, os

from setuptools import setup
from setuptools.command.test import test as TestCommand


PROJECT_ROOT, _ = os.path.split(__file__)
SHORT_VERSION = '3.3'
LONG_VERSION = SHORT_VERSION + '.0'
PROJECT_NAME = 'multiconf'
COPYRIGHT = u"Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT"
PROJECT_AUTHORS = u"Lars Hupfeldt Nielsen"
PROJECT_EMAILS = 'lhn@hupfeldtit.dk'
PROJECT_URL = "https://github.com/lhupfeldt/multiconf"
SHORT_DESCRIPTION = 'Python API providing a set of classes as basis for configuration objects with multiple values per property.'
LONG_DESCRIPTION = open(os.path.join(PROJECT_ROOT, "README.md")).read()


class Test(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to test/test.py")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ""

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, because outside the eggs aren't loaded
        here = os.path.abspath(os.path.dirname(__file__))
        sys.path.insert(0, os.path.join(here, 'test'))
        import test
        errno = test.main(self.pytest_args.split())
        sys.exit(errno)


if __name__ == "__main__":
    setup(
        name=PROJECT_NAME.lower(),
        version=LONG_VERSION,
        author=PROJECT_AUTHORS,
        author_email=PROJECT_EMAILS,
        packages=['multiconf'],
        package_dir={'multiconf': '.'},
        zip_safe=True,
        include_package_data=False,
        install_requires=[],
        test_suite='test',
        tests_require=['pytest', 'pytest-cov', 'demjson'],
        cmdclass={'test': Test},
        url=PROJECT_URL,
        description=SHORT_DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        license='BSD',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 2.7',
            'Topic :: Software Development :: Testing',
        ],
    )
