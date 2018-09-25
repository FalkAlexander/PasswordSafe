project('passwordsafe', 'c',
  version: '3.31.1',
  meson_version: '>= 0.40.0',
)
i18n = import('i18n')
python = import('python3')
project_id = 'org.gnome.PasswordSafe'
contributors = '\n'.join(['Falk Alexander Seidl &lt;fa@terminal.run&gt;', 'Uta Lemke'])

message('Looking for dependencies')
python_bin = python.find_python()
if not python_bin.found()
    error('No valid python3 binary found')
else
    message('Found python3 binary')
endif
dependency('glib-2.0')
dependency('gobject-introspection-1.0', version: '>=1.35.9')
dependency('gtk+-3.0', version :'>=3.20')
dependency('libhandy-0.0', version :'>=0.0.3')

env = environment()

python_dir = join_paths(get_option('prefix'), python.sysconfig_path('purelib'))
LIBEXEC_DIR = join_paths(get_option('prefix'), get_option('libexecdir'))
EXTENSION_DIR = join_paths(get_option('prefix'), get_option('libdir'), meson.project_name())
DATA_DIR = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
bindir = join_paths(get_option('prefix'), get_option('bindir'))

# Python Module Check
pykeepass_dir = join_paths(python_dir, 'pykeepass')
construct_dir = join_paths(python_dir, 'construct')
if run_command('[', '-d', pykeepass_dir, ']').returncode() != 0
    error('Missing dependency pykeepass >= master')
endif

if run_command('[', '-d', construct_dir, ']').returncode() != 0
    error('Missing dependency python-construct >= 2.9.45')
endif

conf = configuration_data()
conf.set('PACKAGE_URL', 'https://gitlab.gnome.org/World/PasswordSafe')
conf.set('DATA_DIR', DATA_DIR)
conf.set('EXTENSION_DIR', EXTENSION_DIR)
conf.set('LOCALE_DIR', join_paths(get_option('prefix'), get_option('datadir'), 'locale'))
conf.set('PYTHON_DIR', python_dir)
conf.set('PYTHON_EXEC_DIR', join_paths(get_option('prefix'), python.sysconfig_path('stdlib')))
conf.set('PYTHON', python_bin.path())
conf.set('libexecdir', LIBEXEC_DIR)
conf.set('VERSION', meson.project_version())
conf.set('CONTRIBUTORS', contributors)

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
