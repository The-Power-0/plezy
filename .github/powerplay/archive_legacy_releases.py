#!/usr/bin/env python3
"""Archive legacy Plezy release listings without deleting assets or tags."""
import argparse
import json
import os
from pathlib import Path
import urllib.request

REPOSITORY = 'The-Power-0/PowerPlay'
ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'docs/archive/pre-powerplay-manifest.json'
REQUEST = ROOT / '.github/powerplay/archive-legacy.request.json'


def api(path, payload=None):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'PowerPlay-Archive',
               'X-GitHub-Api-Version': '2022-11-28'}
    token = os.environ.get('GH_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    body = None if payload is None else json.dumps(payload).encode()
    if body is not None:
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(f'https://api.github.com/repos/{REPOSITORY}/{path}',
                                     data=body, headers=headers,
                                     method='GET' if payload is None else 'PATCH')
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def assets(release):
    return sorted((a['id'], a['name'], a['size']) for a in release['assets'])


def desired(snapshot):
    rollback = snapshot['archive_mode'] == 'public_rollback'
    notice = ('Archived legacy Plezy release. Retained publicly only to preserve the pinned '
              'Home Assistant rollback download URL.' if rollback else
              'Archived legacy Plezy release, preserved as an unpublished draft with its assets and tag intact.')
    return {
        'name': 'Archived — ' + snapshot['name'] + (' (rollback only)' if rollback else ''),
        'body': notice + '\n\nCurrent PowerPlay: https://github.com/' + REPOSITORY +
                '/releases/latest\n\n---\n\n' + (snapshot['body'] or ''),
        'draft': not rollback,
        'prerelease': True,
        'make_latest': 'false',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    request = json.loads(REQUEST.read_text())
    assert manifest['repository'] == REPOSITORY
    assert os.environ.get('GITHUB_REPOSITORY', REPOSITORY) == REPOSITORY
    assert request['confirm'] == 'ARCHIVE_PRE_POWERPLAY_RELEASES'
    assert request['cutoff_tag'] == manifest['cutoff_tag'] == 'powerplay-v1.0.0'
    assert request['release_ids'] == [r['id'] for r in manifest['releases']]
    assert len(set(request['release_ids'])) == len(request['release_ids']) == 4
    expected_latest = manifest['latest_release']
    assert api('releases/latest')['tag_name'] == expected_latest
    baseline = api('releases/tags/powerplay-v1.0.0')
    assert not baseline['draft'] and not baseline['prerelease']
    protected = {tag: api('releases/tags/' + tag)
                 for tag in ['powerplay-v1.0.0', 'powerplay-v1.1.0', 'powerplay-v1.1.1']}
    plans = []
    # Validate every target before changing any release. Keep reruns idempotent.
    for snapshot in manifest['releases']:
        assert not snapshot['tag_name'].startswith('powerplay-')
        assert snapshot['created_at'] < baseline['created_at']
        assert snapshot['archive_mode'] in ('draft', 'public_rollback')
        current = api(f"releases/{snapshot['id']}")
        assert current['tag_name'] == snapshot['tag_name']
        assert not current.get('immutable', False)
        assert assets(current) == assets(snapshot), snapshot['tag_name']
        patch = desired(snapshot)
        untouched = all(current.get(key) == snapshot.get(key)
                        for key in ('name', 'body', 'draft', 'prerelease'))
        archived = all(current.get(key) == patch[key]
                       for key in ('name', 'body', 'draft', 'prerelease'))
        assert untouched or archived, f"Release metadata changed: {snapshot['tag_name']}"
        plans.append((snapshot, patch, archived))
    for snapshot, patch, archived in plans:
        mode = 'public archived prerelease (rollback URL retained)' if not patch['draft'] else 'archived draft'
        print(f"{'ALREADY ARCHIVED' if archived else 'ARCHIVE' if args.apply else 'WOULD ARCHIVE'}: "
              f"{snapshot['tag_name']} -> {mode}; {len(snapshot['assets'])} assets retained")
        if args.apply and not archived:
            result = api(f"releases/{snapshot['id']}", patch)
            assert result['tag_name'] == snapshot['tag_name']
            assert result['draft'] == patch['draft'] and result['prerelease']
            assert assets(result) == assets(snapshot)
    if args.apply:
        for tag, previous in protected.items():
            current = api('releases/tags/' + tag)
            assert current['id'] == previous['id'] and assets(current) == assets(previous)
            assert not current['draft'] and not current['prerelease']
        assert api('releases/latest')['tag_name'] == expected_latest
        rollback = next(r for r in manifest['releases'] if r['archive_mode'] == 'public_rollback')
        apk = next(a for a in rollback['assets'] if a['name'] == 'Plezy.apk')
        with urllib.request.urlopen(urllib.request.Request(apk['url'], method='HEAD'), timeout=30) as response:
            assert response.status == 200
        print(f'VERIFIED: Latest remains {expected_latest}; PowerPlay assets and public Plezy rollback download intact.')
        if summary := os.environ.get('GITHUB_STEP_SUMMARY'):
            Path(summary).write_text('# Legacy releases archived\n\n'
                                     'Three old releases are unpublished drafts. Plezy 2.25.0 is an archived '
                                     'public prerelease to preserve the Home Assistant rollback URL. '
                                     'All original assets and tags remain. Latest: ' + expected_latest + '.\n')
    else:
        print('DRY RUN: no releases changed.')


if __name__ == '__main__':
    main()
