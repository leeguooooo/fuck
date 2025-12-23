import pytest
from fuck.argument_parser import Parser
from fuck.const import ARGUMENT_PLACEHOLDER


def _args(**override):
    args = {'alias': None, 'command': [], 'yes': False,
            'help': False, 'version': False, 'debug': False,
            'force_command': None, 'repeat': False,
            'enable_experimental_instant_mode': False,
            'shell_logger': None, 'setup': False}
    args.update(override)
    return args


@pytest.mark.parametrize('argv, result', [
    (['fuck'], _args()),
    (['fuck', '-a'], _args(alias='fuck')),
    (['fuck', '--alias', '--enable-experimental-instant-mode'],
     _args(alias='fuck', enable_experimental_instant_mode=True)),
    (['fuck', '-a', 'fix'], _args(alias='fix')),
    (['fuck', 'git', 'branch', ARGUMENT_PLACEHOLDER, '-y'],
     _args(command=['git', 'branch'], yes=True)),
    (['fuck', 'git', 'branch', '-a', ARGUMENT_PLACEHOLDER, '-y'],
     _args(command=['git', 'branch', '-a'], yes=True)),
    (['fuck', ARGUMENT_PLACEHOLDER, '-v'], _args(version=True)),
    (['fuck', ARGUMENT_PLACEHOLDER, '--help'], _args(help=True)),
    (['fuck', 'git', 'branch', '-a', ARGUMENT_PLACEHOLDER, '-y', '-d'],
     _args(command=['git', 'branch', '-a'], yes=True, debug=True)),
    (['fuck', 'git', 'branch', '-a', ARGUMENT_PLACEHOLDER, '-r', '-d'],
     _args(command=['git', 'branch', '-a'], repeat=True, debug=True)),
    (['fuck', '-l', '/tmp/log'], _args(shell_logger='/tmp/log')),
    (['fuck', '--shell-logger', '/tmp/log'],
     _args(shell_logger='/tmp/log')),
    (['fuck', '--setup'], _args(setup=True))])
def test_parse(argv, result):
    assert vars(Parser().parse(argv)) == result
