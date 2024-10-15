#!/usr/bin/env bash

set -Eeuo pipefail

# Variables
JSON_FILE="versions.json"
BASE_DOCKER_TAG="inrage/docker-php"

# Fetch the list of available versions
versions=$(jq -r 'keys[]' $JSON_FILE)

# Initialize the output JSON string
matrix_json="{ \"include\": ["

# For each version (e.g., "legacy", "latest")...
for ver in $versions; do

  # Fetch the phpVersions and variants for the current version
  php_versions=$(jq -r ".${ver}.phpVersions[].folder" $JSON_FILE)
  variants=$(jq -r ".${ver}.variants[]" $JSON_FILE)

  # For each PHP version...
  for version in $php_versions; do
    # Fetch the corresponding tag
    tag=$(jq -r --arg phpVersion "$version" ".${ver}.phpVersions[] | select(.folder == \$phpVersion) | .tag" $JSON_FILE)
    
    # For each variant...
    for variant in $variants; do
      # Build the Dockerfile path
      dockerfile_path="${ver}/php${version}/${variant}"

      # Construct the Docker tag
      if [[ $variant == "apache" ]]; then
        if [[ $ver == "beta" ]]; then
          docker_tag="${BASE_DOCKER_TAG}:beta-${tag}"
        else
          docker_tag="${BASE_DOCKER_TAG}:${tag}"
        fi
      else
        docker_tag_variant=${variant#apache-}
        if [[ $ver == "beta" ]]; then
          docker_tag="${BASE_DOCKER_TAG}:beta-${tag}-${docker_tag_variant}"
        else
          docker_tag="${BASE_DOCKER_TAG}:${tag}-${docker_tag_variant}"
        fi
      fi

      # Construct the name
      name="${ver}-${version}-${variant}"

      # Append to the JSON string
      matrix_json+=" {\"context\": \"${dockerfile_path}\", \"tag\": \"${docker_tag}\", \"name\": \"${name}\"},"

    done
  done
done

# Remove the trailing comma and close the JSON string
matrix_json=${matrix_json%,}
matrix_json+=" ] }"

# Display the JSON
echo $matrix_json
