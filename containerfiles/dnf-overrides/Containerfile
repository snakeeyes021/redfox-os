# This Containerfile uses `dnf5` to install packages that frequently suffer from
# dependency drift against the base image (e.g., fast-moving compiler libraries like LLVM).
# Unlike rpm-ostree, DNF allows for granular resolution of these dependencies 
# without forcing a full system upgrade, resolving conflicts automatically.

RUN dnf5 -y install \
    bpftrace \
    && dnf5 clean all