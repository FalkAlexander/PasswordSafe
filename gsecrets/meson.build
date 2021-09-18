conf = configuration_data()

conf.set('APPID', application_id)
conf.set('GETTEXT_PACKAGE', meson.project_name())
conf.set('LOCALE_DIR', join_paths(get_option('prefix'), get_option('datadir'), 'locale'))
conf.set('NAME', project_name)
conf.set('PYTHON', python_bin.path())
conf.set('DATA_DIR', DATA_DIR)
conf.set('PROFILE', profile)
conf.set('APPID', application_id)

configure_file(
  input: 'const.py.in',
  output: 'const.py',
  configuration: conf,
  install_dir: join_paths(python_dir, 'gsecrets'),
  install: true
)

main_conf = configuration_data()
main_conf.set('PYTHON', python_bin.path())
configure_file(
  input: 'main.py.in',
  output: 'secrets',
  configuration: conf,
  install_dir: bindir,
  install: true
)

install_subdir(
  meson.current_source_dir(),
  exclude_directories: ['.mypy_cache', '__pycache__'],
  exclude_files: ['main.py.in', 'const.py.in', 'meson.build'],
  install_dir: python_dir,
)
