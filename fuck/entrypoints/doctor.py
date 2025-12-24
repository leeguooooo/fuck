import os
import re
import six
from .. import const
from ..conf import settings, load_source
from ..shells import shell
from ..system import Path
from ..utils import get_installation_version, which


def _get_config_root():
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME', '~/.config')
    user_dir = Path(xdg_config_home, 'fuck').expanduser()
    legacy_user_dir = Path('~', '.fuck').expanduser()
    if legacy_user_dir.is_dir():
        return legacy_user_dir, True
    return user_dir, False


def _read_settings_file(settings_path):
    if not settings_path.is_file():
        return {}, None
    try:
        module = load_source('fuck_settings', six.text_type(settings_path))
    except Exception as exc:
        return {}, six.text_type(exc)

    values = {}
    for key in const.DEFAULT_SETTINGS.keys():
        if hasattr(module, key):
            values[key] = getattr(module, key)
    return values, None


def _env_settings():
    env_values = {}
    for env, attr in const.ENV_TO_ATTR.items():
        if env in os.environ:
            try:
                env_values[attr] = settings._val_from_env(env, attr)
            except Exception:
                env_values[attr] = os.environ.get(env)
    return env_values


def _format_bool(value):
    return 'yes' if value else 'no'


def _mask_token(value):
    if not value:
        return 'empty'
    return 'set (len={})'.format(len(six.text_type(value)))


def _format_source(attr, env_values, file_values):
    if attr in env_values:
        return 'env'
    if attr in file_values:
        return 'settings'
    return 'default'


def _has_fullwidth_colon(value):
    return u'\uff1a' in six.text_type(value)


def _looks_like_url(value):
    return bool(re.match(r'^https?://', six.text_type(value or '')))


def _check_shell_config(configuration_details):
    if not configuration_details:
        return None, None
    config_path = configuration_details.path
    if '$' in config_path:
        return config_path, None
    resolved = os.path.expanduser(config_path)
    if not os.path.isfile(resolved):
        return resolved, False
    try:
        with open(resolved, 'r') as config_file:
            content = config_file.read()
    except OSError:
        return resolved, False
    return resolved, configuration_details.content in content


def doctor():
    version = get_installation_version()
    shell_info = shell.info()
    alias_name = os.environ.get('FUCK_ALIAS', 'fuck')

    config_root, legacy_config = _get_config_root()
    fish = shell.__class__.__name__.lower() == 'fish'
    env_path = config_root.joinpath('env.fish' if fish else 'env.sh')
    settings_path = config_root.joinpath('settings.py')
    wrapper_path = config_root.joinpath('bin', 'fuck')
    config_details = shell.how_to_configure()
    config_path, config_has_source = _check_shell_config(config_details)

    file_values, file_error = _read_settings_file(settings_path)
    env_values = _env_settings()
    effective = dict(const.DEFAULT_SETTINGS)
    effective.update(file_values)
    effective.update(env_values)

    ai_enabled = bool(effective.get('ai_enabled'))
    ai_url = effective.get('ai_url', '')
    ai_token = effective.get('ai_token', '')
    ai_stream = bool(effective.get('ai_stream'))
    ai_stream_output = bool(effective.get('ai_stream_output'))
    ai_mode = effective.get('ai_mode', '')
    ai_timeout = effective.get('ai_timeout', '')

    warnings = []
    if not settings_path.is_file():
        warnings.append('Settings file missing. Run "fuck setup".')
    if file_error:
        warnings.append('Settings file load error: {}'.format(file_error))
    if not env_path.is_file():
        warnings.append('Env file missing. Run "fuck setup".')
    if config_path and config_has_source is False:
        warnings.append(
            'Shell config does not source env file. Run "source {}" or re-run setup.'
            .format(env_path))
    if ai_enabled and not ai_url:
        warnings.append('AI enabled but AI URL is empty.')
    if ai_url and _has_fullwidth_colon(ai_url):
        warnings.append('AI URL contains a fullwidth colon (U+FF1A). Remove it.')
    if ai_url and six.text_type(ai_url).strip() != six.text_type(ai_url):
        warnings.append('AI URL has leading/trailing whitespace.')
    if ai_url and not _looks_like_url(ai_url):
        warnings.append('AI URL does not look like http(s)://...')
    if ai_enabled and six.text_type(ai_url).startswith('http://127.0.0.1'):
        warnings.append('AI URL is still the default localhost endpoint.')

    print('Doctor:')
    print('- Version: {}'.format(version))
    print('- Shell: {}'.format(shell_info))
    print('- Alias name: {}'.format(alias_name))
    print('- Executable: {}'.format(which('fuck') or 'not found in PATH'))
    print('- Config dir: {} ({})'.format(
        config_root, 'legacy' if legacy_config else 'xdg'))
    print('- Settings file: {} ({})'.format(
        settings_path, 'present' if settings_path.is_file() else 'missing'))
    print('- Env file: {} ({})'.format(
        env_path, 'present' if env_path.is_file() else 'missing'))
    print('- Wrapper: {} ({})'.format(
        wrapper_path, 'present' if wrapper_path.is_file() else 'missing'))
    if config_path:
        if config_has_source is None:
            print('- Shell config: {} (not checked)'.format(config_path))
        else:
            print('- Shell config: {} (source present: {})'.format(
                config_path, _format_bool(config_has_source)))

    print('- AI enabled: {} ({})'.format(
        _format_bool(ai_enabled),
        _format_source('ai_enabled', env_values, file_values)))
    print('- AI URL: {} ({})'.format(
        ai_url,
        _format_source('ai_url', env_values, file_values)))
    print('- AI token: {} ({})'.format(
        _mask_token(ai_token),
        _format_source('ai_token', env_values, file_values)))
    print('- AI timeout: {} ({})'.format(
        ai_timeout,
        _format_source('ai_timeout', env_values, file_values)))
    print('- AI stream: {} ({})'.format(
        _format_bool(ai_stream),
        _format_source('ai_stream', env_values, file_values)))
    print('- AI stream output: {} ({})'.format(
        _format_bool(ai_stream_output),
        _format_source('ai_stream_output', env_values, file_values)))
    print('- AI mode: {} ({})'.format(
        ai_mode,
        _format_source('ai_mode', env_values, file_values)))

    if warnings:
        print('\nWarnings:')
        for warning in warnings:
            print('- {}'.format(warning))
