project('secrets',
        version: '10.3',
        meson_version: '>= 0.64',
        license: 'GPL-3.0-only'
       )
i18n = import('i18n')
python = import('python')
gnome = import('gnome')

project_id = 'org.gnome.World.Secrets'
project_name = 'Secrets'
package_url = 'https://gitlab.gnome.org/World/secrets'
copyright = '© 2018-2024 Falk Alexander Seidl, et al.'
contributors = '\n'.join([
    'Falk Alexander Seidl &lt;fseidl@gnome.org&gt;',
    'Uta Lemke',
    'David Heidelberg',
    'Jean Felder',
    'Maximiliano Sandoval &lt;msandova@gnome.org&gt;',
    'Sebastian Spaeth',
    'Christopher Davis',
    'Jan-Michael Brummer',
                        ])
artists = '\n'.join([
'Christopher Davis',
'Tobias Bernard'
                   ])

message('Looking for dependencies')
# We need pykeepass>=4.1.0 and pyotp>=2.4.0.
python_bin = python.find_installation('python3', modules:[
  'pykeepass',
  'pyotp',
  'validators',
  'zxcvbn_rs_py',
  'PyKCS11',
  'yubico',
])
if not python_bin.found()
  error('No valid python3 binary found')
else
  message('Found python3 binary')
endif

if not python_bin.language_version().version_compare('>= 3.8')
  error('Python 3.8 or newer is required.')
endif


dependency('glib-2.0', version: '>= 2.73.1')
dependency('gio-2.0', version: '>= 2.66')
dependency('gobject-introspection-1.0', version: '>=1.66.0')
dependency('gtk4', version: '>=4.15.3')
dependency('libadwaita-1', version: '>=1.7.alpha')

python_dir = python_bin.get_install_dir()
DATA_DIR = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
bindir = join_paths(get_option('prefix'), get_option('bindir'))


# Profiles
application_id = project_id
if get_option('profile') == 'development'
    profile = 'Devel'
    application_id = '@0@.Devel'.format(application_id)
    version =  ''.join([run_command('git', 'describe', '--long', '--tags', check: false).stdout().strip()])
else
    profile = ''
    version = meson.project_version()
endif

top_source_dir = meson.current_source_dir()
gettext_package = meson.project_name()

subdir('data')
subdir('po')
subdir('gsecrets')
subdir('tests')

gnome.post_install(
  gtk_update_icon_cache: true,
  glib_compile_schemas: true,
  update_desktop_database: true,
  update_mime_database: true,
)
