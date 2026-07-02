#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Updates analyzer version keys in gradle/sonar-plugins.versions.toml for Analysis as a Service.

Environment variables (required):
  RELEASE_VERSION - new version string (e.g. 1.2.3.45678)
  PLUGIN_NAME      - plugin name used when PLUGIN_ARTIFACTS is empty

Environment variables (optional):
  SONAR_PLUGINS_VERSIONS_TOML - path to gradle/sonar-plugins.versions.toml (default: gradle/sonar-plugins.versions.toml)
  PLUGIN_ARTIFACTS            - comma-separated artifact names to update instead of PLUGIN_NAME
"""

import os
import subprocess
import sys

import tomlkit


def candidate_keys(artifact):
    """Yield candidate [versions] keys for an artifact, in resolution order."""
    base = artifact
    if base.endswith('-enterprise'):
        base = base[: -len('-enterprise')]

    if base.startswith('sonar-'):
        if not base.endswith('-plugin'):
            yield f'{base}-plugin'
        yield base
        return

    if not base.endswith('-plugin'):
        yield f'sonar-{base}-plugin'
    yield f'sonar-{base}'


def find_version_key(versions_table, artifact):
    for key in candidate_keys(artifact):
        value = versions_table.get(key)
        if isinstance(value, str):
            return key
    return None


def eprint(message):
    print(message, file=sys.stderr)


def main():
    toml_path = os.environ.get('SONAR_PLUGINS_VERSIONS_TOML', 'gradle/sonar-plugins.versions.toml')
    release_version = os.environ.get('RELEASE_VERSION')
    plugin_name = os.environ.get('PLUGIN_NAME')
    plugin_artifacts = os.environ.get('PLUGIN_ARTIFACTS', '')

    if not release_version:
        eprint('::error::RELEASE_VERSION is required')
        sys.exit(1)
    if not plugin_name:
        eprint('::error::PLUGIN_NAME is required')
        sys.exit(1)

    if not os.path.isfile(toml_path):
        eprint(f'::error::{toml_path} not found.')
        sys.exit(1)

    artifacts = [a.strip() for a in plugin_artifacts.split(',') if a.strip()]
    if not artifacts:
        artifacts = [plugin_name]

    with open(toml_path, 'r', encoding='utf-8') as f:
        original_text = f.read()
    doc = tomlkit.parse(original_text)
    if 'versions' not in doc:
        eprint(f'::error::No [versions] table found in {toml_path}.')
        sys.exit(1)
    versions_table = doc['versions']

    updated_keys = []
    for artifact in artifacts:
        key = find_version_key(versions_table, artifact)
        if key is None:
            tried = ', '.join(candidate_keys(artifact))
            eprint(
                f"::warning::No version key found for artifact '{artifact}' in {toml_path}. "
                f"Tried: {tried}. Skipping."
            )
            continue
        if key in updated_keys:
            continue
        versions_table[key] = release_version
        updated_keys.append(key)
        print(f'Updated {key} to {release_version}')

    if not updated_keys:
        eprint(
            '::warning::No version keys were updated — analyzer likely not yet onboarded to SQAA. '
            'No PR will be created.'
        )
        sys.exit(0)

    with open(toml_path, 'w', encoding='utf-8') as f:
        f.write(tomlkit.dumps(doc))

    print('Showing diff:')
    subprocess.run(['git', '--no-pager', 'diff', '--', toml_path], check=False)


if __name__ == '__main__':
    main()
