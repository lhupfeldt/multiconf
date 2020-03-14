import sys
import os
from os.path import join as jp

import tenjin
from tenjin.helpers import to_str, escape


_HERE = os.path.abspath(os.path.dirname(__file__))


def mk_coveragerc(cov_rc_file_name):
    engine = tenjin.Engine(cache=False)
    major_version = sys.version_info[0]
    minor_version = sys.version_info[1]

    # Note: This naming is duplicated in .travis.yml
    with open(jp(_HERE, '..', cov_rc_file_name), 'w') as cov_rc_file:
        cov_rc_file.write(engine.render(
            jp(_HERE, "coverage_rc.tenjin"), dict(
                to_str=to_str,
                escape=escape,
                major_version=major_version,
                minor_version=minor_version)))

    return cov_rc_file_name


if __name__ == '__main__':
    mk_coveragerc(sys.argv[1])
