"""
Client assets (icons, textures) for patch-Z.MPQ, kept OUT of git.

The repo only lists which files Unbound uses: data/client_assets.txt, one client path per line (for example
Interface\\Icons\\inv_misc_scales_reptileteal01.blp). The files themselves live in a local folder on each PC,
mirroring the client's paths:

    <assets folder>\\Interface\\Icons\\inv_misc_scales_reptileteal01.blp

Default assets folder: <server root>\\unbound-assets (E:\\WoW Solo Server\\unbound-assets), outside the repo, so
nothing in it can be committed. tools/custom_dbc.py packs every listed file it finds there into patch-Z.MPQ
(and warns about listed files that are missing).

Fill the folder from a WoW client install you have locally (each of us uses our own copy):

    python tools/fetch_assets.py --from "T:\\Ascension\\resources\\ascension-live\\Data"

It reads every MPQ archive under that Data folder (read-only), takes each listed file from the archive that
would win in the game (patch-Z over patch-A over patch over base), and writes it into the assets folder. Files
already in the folder are kept (use --force to replace them). Only use art you have the rights to use; don't
commit the assets folder or its files to the repo.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(MODULE)))
sys.path.insert(0, HERE)

from mpq_read import MpqArchive  # noqa: E402

ASSET_LIST = os.path.join(MODULE, 'data', 'client_assets.txt')
DEFAULT_ASSETS = os.path.join(ROOT, 'unbound-assets')


def listed():
    """Client paths from data/client_assets.txt (backslashes, as the client names them)."""
    if not os.path.exists(ASSET_LIST):
        return []
    out = []
    for line in open(ASSET_LIST, encoding='utf-8'):
        line = line.split('#', 1)[0].strip()
        if line:
            out.append(line.replace('/', '\\'))
    return out


def local_path(assets, name):
    return os.path.join(assets, *name.split('\\'))


def load(assets=DEFAULT_ASSETS):
    """({client path: bytes} for the listed files found in the assets folder, [listed files missing])."""
    found, missing = {}, []
    for name in listed():
        path = local_path(assets, name)
        if os.path.isfile(path):
            found[name] = open(path, 'rb').read()
        else:
            missing.append(name)
    return found, missing


def archive_priority(path):
    """Sort key: the archive whose files win in the game sorts last (base, patch, patch-2/3, patch-A..Z). Locale
    patches (Data\\enUS\\patch-enUS-3.MPQ) rank as their unlocalized name, just after it."""
    base = os.path.basename(path).lower()
    locale = re.match(r'patch-[a-z]{4}(?=[-.])', base)
    if locale:
        base = 'patch' + base[len(locale.group(0)):]
    m = re.match(r'patch(?:-(\w+))?\.mpq$', base)
    if not m:
        return (0, base)
    suffix = m.group(1) or ''
    return (1, len(suffix) > 0 and not suffix.isdigit(), suffix.isdigit() and int(suffix) or 0, suffix, bool(locale))


def fetch(data_dir, assets=DEFAULT_ASSETS, force=False):
    wanted = [n for n in listed() if force or not os.path.isfile(local_path(assets, n))]
    if not wanted:
        print('every listed asset is already in', assets)
        return 0
    archives = sorted((os.path.join(d, f) for d, _, fs in os.walk(data_dir) for f in fs
                       if f.lower().endswith('.mpq')), key=archive_priority, reverse=True)
    left = {n.lower(): n for n in wanted}
    for path in archives:
        if not left:
            break
        try:
            archive = MpqArchive(path)
        except (OSError, ValueError) as e:
            print('skip', path, e)
            continue
        for key, name in list(left.items()):
            try:
                data = archive.read(name)
            except ValueError as e:
                print(f'cannot read {name} from {os.path.basename(path)}: {e}')
                continue
            if data is None:
                continue
            dest = local_path(assets, name)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, 'wb') as f:
                f.write(data)
            print(f'{name}  <-  {os.path.basename(path)}')
            del left[key]
        archive.close()
    for name in left.values():
        print('NOT FOUND:', name)
    return len(left)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--from', dest='data_dir', required=True, help="a WoW client's Data folder")
    ap.add_argument('--assets', default=DEFAULT_ASSETS, help=f'local assets folder (default {DEFAULT_ASSETS})')
    ap.add_argument('--force', action='store_true', help='replace files already in the assets folder')
    args = ap.parse_args()
    sys.exit(1 if fetch(args.data_dir, args.assets, args.force) else 0)


if __name__ == '__main__':
    main()
