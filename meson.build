project('passwordsafe', 'c',
  version: '3.99.2',
  meson_version: '>= 0.50.0'
)
i18n = import('i18n')
python = import('python')
project_id = 'org.gnome.PasswordSafe'
contributors = '\n'.join(['Falk Alexander Seidl &lt;fseidl@gnome.org&gt;', 'Uta Lemke'])

message('Looking for dependencies')
python_bin = python.find_installation('python3')
if not python_bin.found()
    error('No valid python3 binary found')
else
    message('Found python3 binary')
endif
dependency('glib-2.0')
dependency('gobject-introspection-1.0', version: '>=1.35.9')
dependency('gtk+-3.0', version :'>=3.20')
dependency('libhandy-1', version :'>=0.90')
dependency('pwquality')

env = environment()

python_dir = join_paths(get_option('prefix'), python_bin.get_install_dir())
LIBEXEC_DIR = join_paths(get_option('prefix'), get_option('libexecdir'))
EXTENSION_DIR = join_paths(get_option('prefix'), get_option('libdir'), meson.project_name())
DATA_DIR = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
bindir = join_paths(get_option('prefix'), get_option('bindir'))


# Python Module Check
python3_required_modules = ['pykeepass', 'construct']

foreach p : python3_required_modules
    # Source: https://docs.python.org/3/library/importlib.html#checking-if-a-module-can-be-imported
    script = 'import importlib.util; import sys; exit(1) if importlib.util.find_spec(\''+ p +'\') is None else exit(0)'
    if run_command(python_bin, '-c', script).returncode() != 0
        error('Required Python3 module \'' + p + '\' not found')
    endif
endforeach


# Profiles
if get_option('profile') == 'development'
    profile = 'Devel'
    name_suffix = ' (Development)'
else
    profile = ''
    name_suffix = ''
endif


conf = configuration_data()
conf.set('PACKAGE_URL', 'https://gitlab.gnome.org/World/PasswordSafe')
conf.set('DATA_DIR', DATA_DIR)
conf.set('EXTENSION_DIR', EXTENSION_DIR)
conf.set('LOCALE_DIR', join_paths(get_option('prefix'), get_option('datadir'), 'locale'))
conf.set('PYTHON_DIR', python_dir)
conf.set('PYTHON_EXEC_DIR', join_paths(get_option('prefix'), python_bin.get_path('stdlib')))
conf.set('PYTHON', python_bin.path())
conf.set('libexecdir', LIBEXEC_DIR)
if get_option('profile') == 'development'
    conf.set('VERSION', ''.join([run_command(['git', 'describe', '--long', '--tags']).stdout(), get_option('profile')]))
else
    conf.set('VERSION', meson.project_version())
endif
conf.set('CONTRIBUTORS', contributors)
conf.set_quoted('PROFILE', profile)

application_id = 'org.gnome.PasswordSafe'
if get_option('profile') == 'development'
  application_id = 'org.gnome.PasswordSafeDevel'
endif
conf.set('APPID', application_id)

subdir('data')
subdir('po')

install_subdir(
  'passwordsafe',
  install_dir: python_dir
)

message('Preparing init file')
configure_file(
  input: 'passwordsafe.in',
  output: 'gnome-passwordsafe',
  configuration: conf,
  install_dir: bindir
)

meson.add_install_script('meson_post_install.py')
