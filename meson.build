project('gc-setup',
  version: '1.0.0',
  meson_version: '>= 0.62.0',
)

python = import('python')
py_installation = python.find_installation('python3')

app_id = 'io.github.gcsetup.GCSetup'
prefix = get_option('prefix')
datadir = prefix / get_option('datadir')
bindir = prefix / get_option('bindir')
pkgdatadir = datadir / 'gc-setup'

# Install Python sources
install_subdir('src', install_dir: pkgdatadir)

# Install data files
install_data('data' / app_id + '.desktop',
  install_dir: datadir / 'applications'
)
install_data('data' / app_id + '.appdata.xml',
  install_dir: datadir / 'metainfo'
)
install_data('data' / 'icons' / app_id + '.svg',
  install_dir: datadir / 'icons' / 'hicolor' / 'scalable' / 'apps'
)

# Install JSON data files
install_data(
  'src' / 'data' / 'catalog.json',
  install_dir: pkgdatadir / 'data'
)

# Generate launcher script
conf = configuration_data()
conf.set('PKGDATADIR', pkgdatadir)
conf.set('APP_ID', app_id)

configure_file(
  input: 'data' / 'gc-setup.in',
  output: 'gc-setup',
  configuration: conf,
  install: true,
  install_dir: bindir,
  install_mode: 'rwxr-xr-x',
)

meson.add_install_script('meson_post_install.py')
