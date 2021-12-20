tests = ['test_element.py']

foreach t: tests
  test(t,
    python_bin,
    args: ['-m', 'pytest'],
    workdir: top_source_dir)
endforeach
