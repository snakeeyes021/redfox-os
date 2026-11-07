#!/usr/bin/env bash
# Tag and clean up feature branches' test images in GHCR.
#
#   feature-images.sh after-build IMAGE BRANCH SHA
#       Run after BlueBuild has pushed BRANCH's build of IMAGE. Gives the new
#       build a fb-<branch>-<sha7>-<fedora> tag, then deletes the branch's
#       older images.
#   feature-images.sh delete IMAGE BRANCH
#       Deletes all of BRANCH's images of IMAGE (the branch is gone).
#
# BlueBuild tags a branch build br-<branch, / as _>-<fedora>, and that tag
# moves to each new build. The fb-… tag stays on its build, so older builds can
# still be found once br-… has moved on. A build is deleted only if every tag
# on it is the branch's br-…/fb-… tag or a BlueBuild commit tag (<sha7>-<fedora>);
# deleting one removes the image index, its child manifests (the image and its
# attestation), and their cosign signature/attestation tags.
#
# Needs: OWNER, GH_TOKEN (packages: write), optionally GH_ACTOR; skopeo, jq, gh;
# cosign for after-build. DRY_RUN=1 lists what would be deleted.
set -euo pipefail

die() { echo "::error::$*" >&2; exit 1; }

[ $# -ge 3 ] || die "usage: $0 after-build IMAGE BRANCH SHA | delete IMAGE BRANCH"
MODE=$1 IMAGE=$2 BRANCH=$3 SHA=${4:-}
: "${OWNER:?OWNER is not set}" "${GH_TOKEN:?GH_TOKEN is not set}"
OWNER=${OWNER,,}
GH_ACTOR=${GH_ACTOR:-$OWNER}
SLUG=${BRANCH//\//_}
REF="ghcr.io/${OWNER}/${IMAGE}"
CREDS="${GH_ACTOR}:${GH_TOKEN}"

reg_tags() { skopeo list-tags --creds "$CREDS" "docker://${REF}" | jq -r '.Tags[]'; }
raw_manifest() { skopeo inspect --raw --creds "$CREDS" "docker://${REF}$1"; }  # $1 = :tag or @digest
digest_of() {  # the digest of a tag: sha256 of its manifest's bytes
    local f sum
    f="$(mktemp)"
    raw_manifest ":$1" > "$f" || { rm -f "$f"; return 1; }
    sum="$(sha256sum < "$f" | cut -d' ' -f1)"
    rm -f "$f"
    echo "sha256:${sum}"
}
children_of() { raw_manifest "@$1" | jq -r '.manifests[]?.digest'; }

# A tag this branch owns: br-<slug>-<fedora> or fb-<slug>-<sha7>-<fedora>.
owned_tag() {
    local t=$1
    case "$t" in
        "br-${SLUG}-"*) [[ ${t#"br-${SLUG}-"} =~ ^[0-9]+$ ]] ;;
        "fb-${SLUG}-"*) [[ ${t#"fb-${SLUG}-"} =~ ^[0-9a-f]{7}-[0-9]+$ ]] ;;
        *) return 1 ;;
    esac
}
# Tags that may be on a build being deleted.
deletable_tag() { owned_tag "$1" || [[ $1 =~ ^[0-9a-f]{7}-[0-9]+$ ]]; }

# Delete the branch's builds, except the one with digest $1 (may be empty).
prune() {
    local keep=$1 tags t d c
    tags="$(reg_tags)" || die "Couldn't list the tags of ${REF}"

    # The branch's builds: image index digest -> its child manifests.
    declare -A builds=() protected=()
    if [ -n "$keep" ]; then
        protected[$keep]=1
        for c in $(children_of "$keep"); do protected[$c]=1; done
    fi
    while IFS= read -r t; do
        if [ -z "$t" ] || ! owned_tag "$t"; then continue; fi
        d="$(digest_of "$t")" || { echo "::warning::Couldn't read ${REF}:${t}"; continue; }
        [ "$d" = "$keep" ] && continue
        builds[$d]=""
    done <<< "$tags"
    if [ "${#builds[@]}" -eq 0 ]; then
        echo "${REF}: no older builds of ${BRANCH} to delete."
        return 0
    fi
    for d in "${!builds[@]}"; do
        builds[$d]="$(children_of "$d" | tr '\n' ' ')"
    done

    # Find the GHCR package versions: each version is one manifest, named by
    # its digest, with its tags. Versions come newest first; a build's
    # signatures are newer than it and its children older, so stop once every
    # manifest we're after has been seen.
    local api owner_type
    owner_type="$(gh api "users/${OWNER}" --jq .type)" || die "Couldn't look up ${OWNER}"
    if [ "$owner_type" = Organization ]; then
        api="orgs/${OWNER}/packages/container/${IMAGE}"
    else
        api="users/${OWNER}/packages/container/${IMAGE}"
    fi
    declare -A want=() id_of=() name_of=() tags_of=() id_of_tag=()
    for d in "${!builds[@]}"; do
        want[$d]=1
        for c in ${builds[$d]}; do [ -n "${protected[$c]:-}" ] || want[$c]=1; done
    done
    local page=1 json n id name vtags missing
    while [ "$page" -le 500 ]; do
        json="$(gh api "${api}/versions?per_page=100&page=${page}")" ||
            die "Couldn't list the versions of ${IMAGE} (does this repository have admin access to the package?)"
        n="$(jq length <<< "$json")"
        [ "$n" -gt 0 ] || break
        while IFS=$'\t' read -r id name vtags; do
            [ -n "$id" ] && [ -n "$name" ] || continue
            id_of[$name]=$id
            name_of[$id]=$name
            tags_of[$name]=$vtags
            for t in $vtags; do id_of_tag[$t]=$id; done
        done < <(jq -r '.[] | [.id, .name, (.metadata.container.tags | join(" "))] | @tsv' <<< "$json")
        missing=0
        for d in "${!want[@]}"; do [ -n "${id_of[$d]:-}" ] || missing=1; done
        [ "$missing" -eq 1 ] || break
        page=$((page + 1))
    done

    local failed=0
    delete_version() {  # $1 = version id, $2 = what it is
        if [ "${DRY_RUN:-}" = 1 ]; then
            echo "  would delete version $1 ($2)"
        elif gh api -X DELETE "${api}/versions/$1" > /dev/null; then
            echo "  deleted version $1 ($2)"
        else
            echo "::warning::Couldn't delete version $1 ($2) of ${IMAGE}"
            return 1
        fi
    }
    # The cosign signature/attestation tags (and OCI referrers) of a manifest.
    delete_signatures() {  # $1 = digest
        local hex=${1#sha256:} t sid sname sc
        for t in "sha256-${hex}" "sha256-${hex}.sig" "sha256-${hex}.att" "sha256-${hex}.sbom"; do
            sid=${id_of_tag[$t]:-}
            [ -n "$sid" ] || continue
            # A referrers index lists manifests of its own.
            sname=${name_of[$sid]}
            for sc in $(children_of "$sname" 2>/dev/null); do
                [ -n "${id_of[$sc]:-}" ] && [ -z "${protected[$sc]:-}" ] || continue
                delete_version "${id_of[$sc]}" "$t child $sc" || failed=1
            done
            delete_version "$sid" "$t" || failed=1
        done
    }

    for d in "${!builds[@]}"; do
        id=${id_of[$d]:-}
        if [ -z "$id" ]; then
            echo "::warning::${REF}@${d} is tagged but wasn't found among the package's versions"
            failed=1
            continue
        fi
        local ok=1
        for t in ${tags_of[$d]}; do
            deletable_tag "$t" || { ok=0; echo "${REF}@${d}: keeping it, it's also tagged ${t}"; }
        done
        [ "$ok" -eq 1 ] || continue
        echo "${REF}: deleting ${d} (${tags_of[$d]})"
        # The index first: if that fails, its children are still in use.
        delete_version "$id" "image index" || { failed=1; continue; }
        delete_signatures "$d"
        for c in ${builds[$d]}; do
            [ -z "${protected[$c]:-}" ] || continue
            if [ -n "${id_of[$c]:-}" ]; then
                delete_version "${id_of[$c]}" "child manifest $c" || failed=1
            fi
            delete_signatures "$c"
        done
    done
    [ "$failed" -eq 0 ] || die "Some of ${BRANCH}'s older images of ${IMAGE} weren't deleted (see the warnings above)."
}

case "$MODE" in
    after-build)
        [ -n "$SHA" ] || die "after-build needs the commit SHA"
        # The build just pushed: the br-<slug>-<fedora> tag with the newest
        # Fedora version (the Hub picks the same one).
        tag="$(reg_tags | while IFS= read -r t; do
            case "$t" in "br-${SLUG}-"*) owned_tag "$t" && echo "$t" ;; esac
        done | sort -V | tail -n1)" || true
        [ -n "$tag" ] || die "No br-${SLUG}-* tag found for ${REF}"
        digest="$(digest_of "$tag")"
        mark="fb-${SLUG}-${SHA:0:7}-${tag##*-}"
        echo "Tagging ${REF}:${tag} (${digest}) as ${mark}"
        if [ "${DRY_RUN:-}" != 1 ]; then
            cosign copy -f \
                --registry-username "$GH_ACTOR" \
                --registry-password "$GH_TOKEN" \
                "${REF}@${digest}" "${REF}:${mark}"
        fi
        prune "$digest"
        ;;
    delete)
        prune ""
        ;;
    *)
        die "Unknown mode '${MODE}' (after-build or delete)"
        ;;
esac
