#!/bin/bash

# Read the current version from VERSION
current_version=$(cat VERSION)

# Split the version into major, minor, and patch components
IFS='.' read -r -a version_parts <<< "$current_version"
major=${version_parts[0]}
minor=${version_parts[1]}
patch=${version_parts[2]}

# Increment the patch version
patch=$((patch + 1))

# Create the new version
new_version="$major.$minor.$patch"

# Write the new version back to VERSION
echo "$new_version" > VERSION

# Output the new version to be used as a variable in the pipeline
echo "##vso[task.setvariable variable=PurplePayNewVersion]$new_version"
