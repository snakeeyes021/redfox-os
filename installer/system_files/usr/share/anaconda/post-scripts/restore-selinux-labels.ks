%post --erroronfail --log=/tmp/anaconda_custom_logs/restore-selinux-labels.log
setenforce 0 || true
restorecon -R /etc/selinux
%end
