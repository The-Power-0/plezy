#!/usr/bin/env python3
"""Preserve historical branch tips as tags, then remove obsolete branch names."""
import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
REPO = 'The-Power-0/PowerPlay'


def api(path, method='GET', payload=None, missing_ok=False):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'PowerPlay-Branch-Archive',
               'X-GitHub-Api-Version': '2022-11-28'}
    if token := os.environ.get('GH_TOKEN'):
        headers['Authorization'] = f'Bearer {token}'
    data = None if payload is None else json.dumps(payload).encode()
    if data is not None:
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(f'https://api.github.com/repos/{REPO}/{path}',
                                     headers=headers, data=data, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return None if response.status == 204 else json.load(response)
    except HTTPError as error:
        if missing_ok and error.code == 404:
            return None
        raise


def tag_tip(name, sha, apply):
    path = 'git/ref/tags/' + quote(name, safe='')
    current = api(path, missing_ok=True)
    if current:
        assert current['object']['type'] == 'commit' and current['object']['sha'] == sha, name
    elif apply:
        api('git/refs', 'POST', {'ref': 'refs/tags/' + name, 'sha': sha})
        saved = api(path)
        assert saved['object']['sha'] == sha
    print(f"{'PRESERVED' if current or apply else 'WOULD TAG'}: {name} -> {sha}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--offline-preview', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'docs/archive/branch-manifest.json').read_text())
    request = json.loads((ROOT / '.github/powerplay/branch-cleanup.request.json').read_text())
    assert manifest['repository'] == REPO == os.environ.get('GITHUB_REPOSITORY', REPO)
    assert request['confirm'] == 'ARCHIVE_OBSOLETE_POWERPLAY_BRANCHES'
    assert manifest['original_default_branch'] == 'ha-shuffle-v2' and manifest['target_default_branch'] == 'main'
    branches = manifest['branches']
    obsolete = [b for b in branches if b['disposition'] == 'archive_and_remove_branch']
    assert len(obsolete) == 27 and len(branches) == 29
    assert all(not b['protected'] and b['name'] not in ('main', 'ha-shuffle-v2') for b in obsolete)
    if args.offline_preview:
        for branch in branches:
            print(f"TAG {branch['archive_tag']} -> {branch['sha']}")
        print('REMOVE obsolete branch names:', ', '.join(b['name'] for b in obsolete))
        print('Retain main; retain ha-shuffle-v2 until main is the default and contains its history.')
        return
    repository = api('')
    assert repository['default_branch'] in ('ha-shuffle-v2', 'main')
    assert api('releases/latest')['tag_name'] == manifest['latest_release']
    open_heads = set()
    for page in range(1, 101):
        pulls = api(f'pulls?state=open&per_page=100&page={page}')
        open_heads.update(p['head']['ref'] for p in pulls)
        if len(pulls) < 100:
            break
    else:
        raise RuntimeError('Too many open PRs to validate branch cleanup')
    plans = []
    for branch in obsolete:
        assert branch['name'] not in open_heads, branch['name']
        current = api('branches/' + quote(branch['name'], safe=''), missing_ok=True)
        if current:
            assert not current['protected'] and current['commit']['sha'] == branch['sha'], branch['name']
            plans.append(branch)
    # Preserve all original tips, including the old main, before removing any names.
    for branch in branches:
        tag_tip(branch['archive_tag'], branch['sha'], args.apply)
    for branch in plans:
        name = branch['name']
        assert api('')['default_branch'] != name
        fresh = api('git/ref/heads/' + quote(name, safe=''))
        assert fresh['object']['sha'] == branch['sha'], name
        if args.apply:
            api('git/refs/heads/' + quote(name, safe=''), 'DELETE')
        print(f"{'REMOVED' if args.apply else 'WOULD REMOVE'} branch: {name}")
    # The old default is removed only after the user/admin has selected main,
    # and only when main actually contains its current commit.
    current_default = api('')['default_branch']
    legacy = api('branches/ha-shuffle-v2', missing_ok=True)
    if current_default == 'main' and legacy and 'ha-shuffle-v2' not in open_heads:
        current_sha = legacy['commit']['sha']
        relation = api(f'compare/{current_sha}...main')
        assert relation['behind_by'] == 0, 'ha-shuffle-v2 has work not contained in main'
        assert not legacy['protected']
        tag_tip('archive/branches/ha-shuffle-v2/' + current_sha[:8], current_sha, args.apply)
        if args.apply:
            api('git/refs/heads/ha-shuffle-v2', 'DELETE')
        print('REMOVED old default branch: ha-shuffle-v2' if args.apply else 'WOULD REMOVE ha-shuffle-v2')
    elif current_default != 'main':
        print('READY FOR ADMIN: select main as the default branch; ha-shuffle-v2 remains until then.')
    assert api('releases/latest')['tag_name'] == manifest['latest_release']
    remaining = api('branches?per_page=100')
    print('REMAINING BRANCHES:', ', '.join(b['name'] for b in remaining))
    if summary := os.environ.get('GITHUB_STEP_SUMMARY'):
        Path(summary).write_text('# Branch archive\n\nOriginal branch tips are preserved under '
                                 '`archive/branches/…` tags. No releases or application source were changed.\n\n'
                                 'Default branch: `' + current_default + '`. Remaining branches: ' +
                                 ', '.join('`' + b['name'] + '`' for b in remaining) + '.\n')


if __name__ == '__main__':
    main()
