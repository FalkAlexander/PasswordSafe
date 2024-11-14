envs = [
  'G_TEST_SRCDIR=' + meson.current_source_dir(),
  'G_TEST_BUILDDIR=' + meson.current_build_dir(),
]

test(
  'Test Element',
  python_bin,
  args: files('test_element.py'),
  env: envs
)

test(
  'Test Password Generator',
  python_bin,
  args: files('test_password_generator.py'),
  env: envs
)
