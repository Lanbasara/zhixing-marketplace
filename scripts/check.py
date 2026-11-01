#!/usr/bin/env python3
"""Validate Zhixing catalogs and authenticate new records against local source Git objects."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

VERSION = re.compile(r'(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)')
SHA = re.compile(r'[0-9a-f]{40}')
URL = 'https://github.com/Lanbasara/zhixing.git'


def read(path):
    if path.is_symlink() or path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError('invalid catalog file')
    return json.loads(path.read_bytes())


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                          check=True, timeout=60).stdout


def validate(root, source, base):
    ledger = read(root / 'releases.json')
    if set(ledger) != {'format', 'releases'} or ledger['format'] != 1:
        raise ValueError('invalid release ledger')
    history = ledger['releases']
    if not isinstance(history, list) or len(history) > 1000:
        raise ValueError('invalid history')
    versions = []
    for row in history:
        if not isinstance(row, dict) or set(row) != {'version', 'commit', 'timestamp', 'dsh'}:
            raise ValueError('invalid release record')
        if not isinstance(row['version'], str) or not VERSION.fullmatch(row['version']):
            raise ValueError('invalid version')
        if not isinstance(row['commit'], str) or not SHA.fullmatch(row['commit']):
            raise ValueError('invalid commit')
        if type(row['timestamp']) is not int or row['timestamp'] <= 0:
            raise ValueError('invalid timestamp')
        if not isinstance(row['dsh'], str) or len(row['dsh']) > 128:
            raise ValueError('invalid host compatibility range')
        versions.append(tuple(map(int, row['version'].split('.'))))
    if versions != sorted(set(versions), reverse=True):
        raise ValueError('release history must be unique and descending')
    if not SHA.fullmatch(base):
        raise ValueError('base must be a full commit SHA')
    previous = [] if base == '0' * 40 else json.loads(git(root, 'show', base + ':releases.json'))['releases']
    added = len(history) - len(previous)
    if added < 0 or history[added:] != previous:
        raise ValueError('published history cannot be rewritten or removed')
    records = []
    descriptions = []
    for host in ('.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json', 'dsh/index.json'):
        document = read(root / host)
        if host == 'dsh/index.json':
            if document.get('format') != 1 or not document.get('title'):
                raise ValueError('invalid DSH catalog')
        elif document.get('name') != 'zhixing':
            raise ValueError('invalid market identity')
        plugins = document.get('plugins')
        if not isinstance(plugins, list) or len(plugins) != bool(history):
            raise ValueError('catalog does not match release availability')
        if not history:
            continue
        plugin = plugins[0]
        if plugin.get('name') != 'zhixing':
            raise ValueError('unexpected product')
        descriptions.append(plugin.get('description'))
        latest = history[0]
        if host == 'dsh/index.json':
            expected = [{'version': r['version'], 'publishTimestamp': r['timestamp'],
                         'engines': {'dsh': r['dsh']},
                         'source': {'type': 'git', 'url': URL, 'commit': r['commit'], 'path': 'plugin'}}
                        for r in history]
            if plugin.get('versions') != expected:
                raise ValueError('DSH versions differ from authenticated history')
        else:
            path = './plugin' if host.startswith('.agents') else 'plugin'
            expected = {'source': 'git-subdir', 'url': URL, 'path': path,
                        'sha': latest['commit'], 'ref': 'v' + latest['version']}
            if plugin.get('source') != expected:
                raise ValueError('host catalog is not pinned to the same release')
            if host.startswith('.agents') and (
                    plugin.get('policy') != {'installation': 'AVAILABLE', 'authentication': 'ON_USE'}
                    or plugin.get('category') != 'Productivity'):
                raise ValueError('invalid Codex install policy')
    if descriptions and (len(set(descriptions)) != 1 or not descriptions[0]):
        raise ValueError('host descriptions disagree')
    for row in history[:added]:
        if source is None:
            raise ValueError('new releases require a local source checkout')
        tag = 'refs/tags/v' + row['version']
        if git(source, 'cat-file', '-t', tag).strip() != b'tag':
            raise ValueError('expected an annotated release tag')
        commit = git(source, 'rev-parse', tag + '^{commit}').decode().strip()
        if commit != row['commit']:
            raise ValueError('release tag differs from indexed commit')
        git(source, 'merge-base', '--is-ancestor', commit, 'refs/remotes/origin/main')
        package = json.loads(git(source, 'show', commit + ':plugin/package.json'))
        version = git(source, 'show', commit + ':VERSION').decode().strip()
        timestamp = int(git(source, 'show', '-s', '--format=%ct', commit))
        if (package['name'] != 'zhixing' or version != row['version'] or package['version'] != version
                or package['engines']['dsh'] != row['dsh'] or timestamp != row['timestamp']):
            raise ValueError('release record differs from tagged product metadata')
        if row == history[0] and package['description'] != descriptions[0]:
            raise ValueError('description differs from released product')
    return len(history)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source', type=Path)
    parser.add_argument('--base', default='0' * 40)
    args = parser.parse_args()
    try:
        count = validate(args.root, args.source, args.base)
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f'PASS: three pinned host catalogs, {count} releases, preserved history')
