project('passwordsafe',
        version: '5.alpha',
        meson_version: '>= 0.51.0'
       )
i18n = import('i18n')
python = import('python')
project_id = 'org.gnome.PasswordSafe'
contributors = '\n'.join([
    'Falk Alexander Seidl &lt;fseidl@gnome.org&gt;',
    'Uta Lemke',
    'David Heidelberg',
    'Jean Felder',
    'Maximiliano Sandoval',
    'Sebastian Spaeth',
    'Christopher Davis',
                        ])

message('Looking for dependencies')
python_bin = python.find_installation('python3', modules:['pykeepass'])
if not python_bin.found()
  error('No valid python3 binary found')
else
  message('Found python3 binary')
endif

if not python_bin.language_version().version_compare('>= 3.7')
  error('Python 3.7 or newer is required.')
endif


dependency('glib-2.0')
dependency('gobject-introspection-1.0', version: '>=1.35.9')
dependency('gtk+-3.0', version: '>=3.24.1')
dependency('libhandy-1', version: '>=1.0.0')
dependency('pwquality')

env = environment()

python_dir = python_bin.get_install_dir()
LIBEXEC_DIR = join_paths(get_option('prefix'), get_option('libexecdir'))
EXTENSION_DIR = join_paths(get_option('prefix'), get_option('libdir'), meson.project_name())
DATA_DIR = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
bindir = join_paths(get_option('prefix'), get_option('bindir'))


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
  exclude_directories: ['.mypy_cache', ' __pycache__'],
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
