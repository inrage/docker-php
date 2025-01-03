#!/usr/bin/env bash
set -Eeuo pipefail

jqt='.jq-template.awk'
if [ -n "${BASHBREW_SCRIPTS:-}" ]; then
	jqt="$BASHBREW_SCRIPTS/jq-template.awk"
elif [ "$BASH_SOURCE" -nt "$jqt" ]; then
	# https://github.com/docker-library/bashbrew/blob/master/scripts/jq-template.awk
	wget -qO "$jqt" 'https://github.com/docker-library/bashbrew/raw/9f6a35772ac863a0241f147c820354e4008edf38/scripts/jq-template.awk'
fi

generated_warning() {
	cat <<-EOH
		#
		# NOTE: THIS DOCKERFILE IS GENERATED VIA "apply-templates.sh"
		#
		# PLEASE DO NOT EDIT IT DIRECTLY.
		#

	EOH
}

version="latest"
export version

phpVersions="$(jq -r '.[env.version].phpVersions | map(.folder | @sh) | join(" ")' versions.json)"
eval "phpVersions=( $phpVersions )"

variants="$(jq -r '.[env.version].variants | map(@sh) | join(" ")' versions.json)"
eval "variants=( $variants )"

for phpVersion in "${phpVersions[@]}"; do
    export phpVersion

    tag="$(jq -r --arg phpVersion "$phpVersion" '.[env.version].phpVersions[] | select(.folder == $phpVersion) | .tag' versions.json)"
    export tag

    for variant in "${variants[@]}"; do
        export variant

        dir="$version/php$phpVersion/$variant"
        mkdir -p "$dir"

        echo "processing $dir ..."

        {
          generated_warning
          gawk -f "$jqt" Dockerfile
        } > "$dir/Dockerfile"

        cp -aR templates "$dir/"
        cp -aR bin "$dir/"
        cp -a cron-entrypoint.sh "$dir/"
        cp -a docker-entrypoint.sh "$dir/"
    done
done
