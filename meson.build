project('passwordsafe',
        version: '5.0',
        meson_version: '>= 0.51.0'
       )
i18n = import('i18n')
python = import('python')
project_id = 'org.gnome.PasswordSafe'
project_name = 'Password Safe'
package_url = 'https://gitlab.gnome.org/World/PasswordSafe'
copyright = '© 2018-2021 Falk Alexander Seidl, et al.'
contributors = '\n'.join([
    'Falk Alexander Seidl &lt;fseidl@gnome.org&gt;',
    'Uta Lemke',
    'David Heidelberg',
    'Jean Felder',
    'Maximiliano Sandoval',
    'Sebastian Spaeth',
    'Christopher Davis',
                        ])
artists = '\n'.join([
'Christopher Davis',
'Tobias Bernard'
                   ])

message('Looking for dependencies')
python_bin = python.find_installation('python3', modules:['pykeepass', 'pyotp'])
if not python_bin.found()
  error('No valid python3 binary found')
else
  message('Found python3 binary')
endif

if not python_bin.language_version().version_compare('>= 3.7')
  error('Python 3.7 or newer is required.')
endif


dependency('glib-2.0', version: '>= 2.66')
dependency('gio-2.0', version: '>= 2.66')
dependency('gobject-introspection-1.0', version: '>=1.66.0')
dependency('gtk4', version: '>=4.0.0')
dependency('libadwaita-1', version: '>=1.0.0')
dependency('pwquality')

python_dir = python_bin.get_install_dir()
DATA_DIR = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
bindir = join_paths(get_option('prefix'), get_option('bindir'))


# Profiles
application_id = project_id
if get_option('profile') == 'development'
    profile = 'Devel'
    application_id = '@0@.Devel'.format(application_id)
    version =  ''.join([run_command(['git', 'describe', '--long', '--tags']).stdout().strip()])
else
    profile = ''
    version = meson.project_version()
endif

subdir('data')
subdir('po')
subdir('passwordsafe')

conf = configuration_data()
conf.set('PYTHON', python_bin.path())
configure_file(
  input: 'passwordsafe.in',
  output: 'gnome-passwordsafe',
  configuration: conf,
  install_dir: bindir
)

pylint = find_program('pylint', required: false)
if pylint.found()
  test (
    'Pylint tests',
    pylint,
    args: ['--rcfile=@0@'.format(join_paths(meson.current_source_dir (), '.pylintrc')),
          join_paths(python_dir, 'passwordsafe')],
    timeout: 300,
  )
endif

meson.add_install_script('meson_post_install.py')
