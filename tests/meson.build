envs = [
  'G_TEST_SRCDIR=' + meson.current_source_dir(),
  'G_TEST_BUILDDIR=' + meson.current_build_dir(),
]

test(
  'test_element.py',
  python_bin,
  args: ['-m', 'pytest'],
  workdir: top_source_dir,
  env: envs
)
