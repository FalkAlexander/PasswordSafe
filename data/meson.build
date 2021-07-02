gnome = import('gnome')

message('Compiling resources')

about_conf = configuration_data()
about_conf.set('PACKAGE_URL', package_url)
about_conf.set('CONTRIBUTORS', contributors)
about_conf.set('ARTISTS', artists)
about_conf.set('APPID', application_id)
about_conf.set('VERSION', version)
about_conf.set('COPYRIGHT', copyright)

gnome.compile_resources(
  meson.project_name(),
  meson.project_name() + '.gresource.xml',
  gresource_bundle: true,
  source_dir: '.',
  install_dir: DATA_DIR,
  install: true,
  dependencies: configure_file (
    input: 'about_dialog.ui.in',
    output: 'about_dialog.ui',
    configuration: about_conf
  )
)

# Installing the schema file
gschema_conf = configuration_data()
gschema_conf.set('APP_ID', application_id)
gschema_conf.set('GETTEXT_PACKAGE', meson.project_name())
configure_file(
    input: '@0@.gschema.xml.in'.format(project_id),
    output: '@0@.gschema.xml'.format(application_id),
    configuration: gschema_conf,
    install: true,
    install_dir: 'share/glib-2.0/schemas'
)

# Install mimetype file
install_data(
  project_id + '.xml',
  install_dir: 'share/mime/packages'
)

desktop_conf = configuration_data()
desktop_conf.set('ICON', application_id)
desktop = i18n.merge_file(
  'desktop',
  input: configure_file(
    input: files('org.gnome.PasswordSafe.desktop.in.in'),
    output: 'org.gnome.PasswordSafe.desktop.in',
    configuration: desktop_conf
  ),
  output: '@0@.desktop'.format(application_id),
  po_dir: join_paths(meson.source_root(), 'po'),
  type: 'desktop',
  install: true,
  install_dir: join_paths(get_option('prefix'), get_option('datadir'), 'applications')
)

# Validating the desktop file
desktop_file_validate = find_program('desktop-file-validate', required:false)
if desktop_file_validate.found()
  test (
    'Validate desktop file',
    desktop_file_validate,
    args: join_paths(meson.current_build_dir (), application_id + '.desktop')
  )
endif

appdata_conf = configuration_data()
appdata_conf.set('APPID', application_id)
appdata_conf.set('GETTEXT_PACKAGE', meson.project_name())
appdata_conf.set('NAME', project_name)
appdata = i18n.merge_file(
  'appdata',
  input: configure_file(
    input: files('org.gnome.PasswordSafe.appdata.xml.in.in'),
    output: 'org.gnome.PasswordSafe.appdata.xml.in',
    configuration: appdata_conf
  ),
  output: application_id + '.appdata.xml',
  install: true,
  install_dir: join_paths(join_paths('share'), 'metainfo'),
  po_dir: join_paths(meson.source_root(), 'po')
)


# Validating the appdata file
appstreamcli = find_program('appstream-util', required: false)
if appstreamcli.found()
  test (
    'Validate appdata file',
    appstreamcli,
    args: ['validate-relax', '--nonet', join_paths(meson.current_build_dir (), application_id + '.appdata.xml')]
  )
endif

# Validating schemas
compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file', compile_schemas,
    args: ['--strict', '--dry-run', meson.current_source_dir()]
  )
endif

subdir('icons')
