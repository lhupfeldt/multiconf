import sys, os

from setuptools import setup
from setuptools.command.test import test as TestCommand


PROJECT_ROOT, _ = os.path.split(__file__)
PROJECT_NAME = 'multiconf'
COPYRIGHT = u"Copyright (c) 2012 - 2016 Lars Hupfeldt Nielsen, Hupfeldt IT"
PROJECT_AUTHORS = u"Lars Hupfeldt Nielsen"
PROJECT_EMAILS = 'lhn@hupfeldtit.dk'
PROJECT_URL = "https://github.com/lhupfeldt/multiconf"
SHORT_DESCRIPTION = 'Python API providing a set of classes as basis for configuration objects with multiple values per attribute.'
LONG_DESCRIPTION = open(os.path.join(PROJECT_ROOT, "README.rst")).read()


class Test(TestCommand):
    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import test.run
        sys.exit(test.run.main(self.test_args))


major_version = sys.version_info[0]
if major_version < 3:
    py_version_requires = ['enum34>=1.1']
else:
    py_version_requires = ['typing-inspect>=0.2.0']


if __name__ == "__main__":
    setup(
        name=PROJECT_NAME.lower(),
        version_command=('git describe', 'pep440-git'),
        author=PROJECT_AUTHORS,
        author_email=PROJECT_EMAILS,
        packages=['multiconf'],
        package_dir={'multiconf': 'multiconf'},
        zip_safe=True,
        include_package_data=False,
        install_requires=[] + py_version_requires,
        setup_requires='setuptools-version-command~=2.2',
        test_suite='test',
        tests_require=['pytest>=3.0.5', 'pytest-cov>=2.4.0', 'demjson~=2.2.3', 'tenjin~=1.1'],
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
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Topic :: System :: Installation/Setup',
            'Topic :: Software Development :: Testing',
        ],
    )
