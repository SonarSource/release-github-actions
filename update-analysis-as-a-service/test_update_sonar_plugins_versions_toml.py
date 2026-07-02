#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for update_sonar_plugins_versions_toml.py
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tomlkit

from update_sonar_plugins_versions_toml import candidate_keys, main


# Verbatim copy of gradle/sonar-plugins.versions.toml as introduced by
# sonar-analysis-as-a-service PR #613, so round-trip tests exercise the real file shape.
FIXTURE = '''# Versions of the Sonar language analyzer plugins.
#
# This catalog is intentionally kept separate from gradle/libs.versions.toml so that the
# relevant language squads can own these version bumps via .github/CODEOWNERS without
# owning every other dependency. It is exposed to build scripts as the `sonarAnalyzers`
# version catalog (registered in settings.gradle.kts).
[versions]
sonar-cfamily = "6.82.1.100194"
sonar-dart = "1.7.0.4715"
sonar-dotnet = "10.27.0.140913"
sonar-dre = "2.6.0.14497"
sonar-go = "1.40.0.6765"
sonar-html = "3.24.0.7341"
sonar-iac = "2.12.0.21417"
sonar-java = "8.25.0.42802"
sonar-java-symbolic-execution = "8.18.0.242"
sonar-plsql = "3.18.1.230"
sonar-python = "5.23.0.33560"
sonar-security = "11.36.0.47442"
sonar-kotlin = "3.7.0.9514"
sonar-swift = "5.5.0.13021"
sonar-text = "2.41.0.10709"
sonar-xml = "2.16.0.7616"
# A3S .NET integration package (A3S.NET nupkg)
a3s-dotnet = "1.4.0.803"

[libraries]
sonar-cfamily-plugin = { module = "com.sonarsource.cpp:sonar-cfamily-plugin", version.ref = "sonar-cfamily" }
sonar-csharp-enterprise-plugin = { module = "com.sonarsource.dotnet:sonar-csharp-enterprise-plugin", version.ref = "sonar-dotnet" }
sonar-vbnet-enterprise-plugin = { module = "com.sonarsource.dotnet:sonar-vbnet-enterprise-plugin", version.ref = "sonar-dotnet" }
sonar-dart-plugin = { module = "com.sonarsource.dart:sonar-dart-plugin", version.ref = "sonar-dart" }
sonar-dre-plugin = { module = "com.sonarsource.dre:sonar-dre-plugin", version.ref = "sonar-dre" }
sonar-go-plugin = { module = "com.sonarsource.go:sonar-go-enterprise-plugin", version.ref = "sonar-go" }
sonar-html-plugin = { module = "org.sonarsource.html:sonar-html-plugin", version.ref = "sonar-html" }
sonar-iac-plugin = { module = "com.sonarsource.iac:sonar-iac-enterprise-plugin", version.ref = "sonar-iac" }
sonar-java-plugin = { module = "org.sonarsource.java:sonar-java-plugin", version.ref = "sonar-java" }
sonar-java-symbolic-execution-plugin = { module = "org.sonarsource.java:sonar-java-symbolic-execution-plugin", version.ref = "sonar-java-symbolic-execution" }
sonar-kotlin-plugin = { module = "org.sonarsource.kotlin:sonar-kotlin-plugin", version.ref = "sonar-kotlin" }
sonar-plsql-plugin = { module = "com.sonarsource.plsql:sonar-plsql-plugin", version.ref = "sonar-plsql" }
sonar-python-plugin = { module = "com.sonarsource.python:sonar-python-enterprise-plugin", version.ref = "sonar-python" }
sonar-security-csharp-frontend-plugin = { module = "com.sonarsource.security:sonar-security-csharp-frontend-plugin", version.ref = "sonar-security" }
sonar-security-vbnet-frontend-plugin  = { module = "com.sonarsource.security:sonar-security-vbnet-frontend-plugin",  version.ref = "sonar-security" }
sonar-security-go-frontend-plugin = { module = "com.sonarsource.security:sonar-security-go-frontend-plugin", version.ref = "sonar-security" }
sonar-security-java-frontend-plugin = { module = "com.sonarsource.security:sonar-security-java-frontend-plugin", version.ref = "sonar-security" }
sonar-security-kotlin-frontend-plugin = { module = "com.sonarsource.security:sonar-security-kotlin-frontend-plugin", version.ref = "sonar-security" }
sonar-security-plugin = { module = "com.sonarsource.security:sonar-security-plugin", version.ref = "sonar-security" }
sonar-swift-plugin = { module = "com.sonarsource.swift:sonar-swift-plugin", version.ref = "sonar-swift" }
sonar-text-plugin = { module = "com.sonarsource.text:sonar-text-enterprise-plugin", version.ref = "sonar-text" }
sonar-xml-plugin = { module = "org.sonarsource.xml:sonar-xml-plugin", version.ref = "sonar-xml" }
'''


class TestCandidateKeys(unittest.TestCase):

    def test_sonar_prefixed_without_plugin_suffix(self):
        self.assertEqual(list(candidate_keys('sonar-java')), ['sonar-java-plugin', 'sonar-java'])

    def test_sonar_prefixed_with_plugin_suffix(self):
        self.assertEqual(list(candidate_keys('sonar-java-plugin')), ['sonar-java-plugin'])

    def test_bare_name(self):
        self.assertEqual(list(candidate_keys('java')), ['sonar-java-plugin', 'sonar-java'])

    def test_enterprise_suffix_stripped(self):
        self.assertEqual(list(candidate_keys('go-enterprise')), ['sonar-go-plugin', 'sonar-go'])


class TestUpdateSonarPluginsVersionsToml(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.toml_path = os.path.join(self.tmpdir, 'sonar-plugins.versions.toml')
        with open(self.toml_path, 'w', encoding='utf-8') as f:
            f.write(FIXTURE)
        self.env = {
            'SONAR_PLUGINS_VERSIONS_TOML': self.toml_path,
        }

    def run_main(self, **env_overrides):
        env = dict(self.env, **env_overrides)
        old_environ = dict(os.environ)
        old_argv = sys.argv
        os.environ.clear()
        os.environ.update(env)
        try:
            main()
        except SystemExit as exc:
            return exc.code
        finally:
            os.environ.clear()
            os.environ.update(old_environ)
            sys.argv = old_argv
        return None

    def read_toml(self):
        with open(self.toml_path, 'r', encoding='utf-8') as f:
            return tomlkit.parse(f.read())

    def test_normal_update(self):
        self.run_main(PLUGIN_NAME='dre', RELEASE_VERSION='2.7.0.1')
        doc = self.read_toml()
        self.assertEqual(doc['versions']['sonar-dre'], '2.7.0.1')
        self.assertEqual(doc['libraries']['sonar-dre-plugin']['version']['ref'], 'sonar-dre')

    def test_family_key_non_collision(self):
        self.run_main(PLUGIN_NAME='java', RELEASE_VERSION='9.0.0.2')
        doc = self.read_toml()
        self.assertEqual(doc['versions']['sonar-java'], '9.0.0.2')
        self.assertEqual(doc['versions']['sonar-java-symbolic-execution'], '8.18.0.242')

    def test_enterprise_suffix_stripping(self):
        self.run_main(PLUGIN_NAME='go', PLUGIN_ARTIFACTS='go-enterprise', RELEASE_VERSION='1.41.0.1')
        doc = self.read_toml()
        self.assertEqual(doc['versions']['sonar-go'], '1.41.0.1')

    def test_multi_artifact_update(self):
        self.run_main(PLUGIN_NAME='java', PLUGIN_ARTIFACTS='java,java-symbolic-execution', RELEASE_VERSION='9.1.0.3')
        doc = self.read_toml()
        self.assertEqual(doc['versions']['sonar-java'], '9.1.0.3')
        self.assertEqual(doc['versions']['sonar-java-symbolic-execution'], '9.1.0.3')

    def test_blank_artifacts_falls_back_to_plugin_name(self):
        self.run_main(PLUGIN_NAME='python', PLUGIN_ARTIFACTS=' , ', RELEASE_VERSION='5.24.0.5')
        doc = self.read_toml()
        self.assertEqual(doc['versions']['sonar-python'], '5.24.0.5')

    def test_unknown_plugin_skipped_without_failing(self):
        exit_code = self.run_main(PLUGIN_NAME='nonexistent-plugin-xyz', RELEASE_VERSION='1.0.0.1')
        self.assertEqual(exit_code, 0)
        doc = self.read_toml()
        self.assertEqual(doc['versions']['sonar-python'], '5.23.0.33560')

    def test_mixed_known_and_unknown_artifacts(self):
        self.run_main(PLUGIN_NAME='python', PLUGIN_ARTIFACTS='python,nonexistent-plugin-xyz', RELEASE_VERSION='5.24.0.6')
        doc = self.read_toml()
        self.assertEqual(doc['versions']['sonar-python'], '5.24.0.6')

    def test_libraries_table_never_mutated(self):
        before = self.read_toml()['libraries']
        self.run_main(PLUGIN_NAME='java', RELEASE_VERSION='9.0.0.2')
        after = self.read_toml()['libraries']
        self.assertEqual(tomlkit.dumps(before), tomlkit.dumps(after))

    def test_round_trip_preserves_header_and_structure(self):
        with open(self.toml_path, 'r', encoding='utf-8') as f:
            original_text = f.read()
        self.run_main(PLUGIN_NAME='dre', RELEASE_VERSION='2.7.0.1')
        with open(self.toml_path, 'r', encoding='utf-8') as f:
            updated_text = f.read()

        original_lines = original_text.splitlines()
        updated_lines = updated_text.splitlines()
        self.assertEqual(len(original_lines), len(updated_lines))

        header_lines = [line for line in original_lines if line.startswith('#')]
        for line in header_lines:
            self.assertIn(line, updated_lines)

        changed = [
            (a, b) for a, b in zip(original_lines, updated_lines) if a != b
        ]
        self.assertEqual(len(changed), 1)
        self.assertEqual(changed[0], ('sonar-dre = "2.6.0.14497"', 'sonar-dre = "2.7.0.1"'))


if __name__ == '__main__':
    unittest.main()
