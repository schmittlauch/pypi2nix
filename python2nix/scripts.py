from distutils2.errors import IrrationalVersionError
from distutils2.pypi.errors import ProjectNotFound
from distutils2.pypi.simple import Crawler
from distutils2.version import suggest_normalized_version
from python2nix.config import HARD_REQUIREMENTS
from python2nix.config import IGNORE_PACKAGES
from python2nix.config import INSTALL_COMMAND
from python2nix.config import PLONEDEPS
from python2nix.config import POST_TMPL
from python2nix.config import PRE_TMPL
from python2nix.config import SYSTEM_PACKAGES
from python2nix.config import TMPL
from python2nix.utils import nix_metadata
from python2nix.utils import to_dict

import argparse
import sys


def buildout2nix():
    parser = argparse.ArgumentParser(
        description='Create a Nix package attribute set from a python buildout'
    )
    parser.add_argument(
        '-b',
        '--buildout-path',
        help='path to a buildout executable (not implemented)',
    )
    parser.add_argument(
        '-i',
        '--input',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin,
        help=(
            'path to a file which contains one package name followed by a '
            'version number per line'
        )
    )    
    parser.add_argument(
        '-o',
        '--output',
        nargs='?',
        type=argparse.FileType('wb', 0),
        default=sys.stdout,
        help='path to output file (not implemented)',
    )

    args = parser.parse_args()

    if args.buildout_path is not None:
        raise Exception("Not implemented")
    else:
        eggs = to_dict(args.input.read())

    pypi = Crawler()

    bad_eggs = []
    not_found = []
    version_error = []
    print PRE_TMPL

    for nixname in sorted(eggs.keys()):
        if nixname in SYSTEM_PACKAGES: continue
        if nixname in IGNORE_PACKAGES: continue
        egg = eggs[nixname]
        version = suggest_normalized_version(egg['version'])
        name = egg['name']
        if egg['extras']:
            name += '-'.join(egg['extras'])
        name += '-' + egg['version']
        try:
            egg_release = pypi.get_release(egg['name'] + '==' + version)
        except ProjectNotFound:
            not_found.append(egg['name'])
        except IrrationalVersionError:
            version_error.append(egg['name'])
        egg_dist = egg_release.dists['sdist'].url
        url = egg_dist['url']
        url = url.replace("http://a.pypi", "http://pypi")
        metadata = nix_metadata(egg_release)
        url = url.replace(name, "${name}")
        build_inputs = ''
        if url.endswith(".zip"):
            build_inputs = "\n    buildInputs = [ pkgs.unzip ];\n"
        propagated_build_inputs = ''
        if nixname in HARD_REQUIREMENTS.keys():
            propagated_build_inputs = (
                "\n    propagatedBuildInputs = [ {0} ];\n"
        ).format(HARD_REQUIREMENTS[nixname])
        print TMPL % {'nixname': nixname,
                      'name': name,
                      'url': url,
                      'hashname': egg_dist['hashname'],
                      'hashval': egg_dist['hashval'],
                      'build_inputs': build_inputs,
                      'propagated_build_inputs': propagated_build_inputs,
                      'install_command': INSTALL_COMMAND,
                      'metadata': metadata,
        }
    print POST_TMPL
    # print "# Not Found: {0}\n# Version Error: {1}".format(
    #     not_found, version_error)
