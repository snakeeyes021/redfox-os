install_data('style.css', install_dir: pkgdatadir)
install_subdir('layouts', install_dir: pkgdatadir)
install_subdir('manual', install_dir: pkgdatadir)

install_data(app_id + '.desktop',
  install_dir: get_option('datadir') / 'applications')
install_data(app_id + '.metainfo.xml',
  install_dir: get_option('datadir') / 'metainfo')
install_subdir('icons/hicolor',
  install_dir: get_option('datadir') / 'icons')
