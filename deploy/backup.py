"""Backup consistente via API SQLite, inclusive com WAL ativo."""
import argparse
import os
import sqlite3
from contextlib import closing
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('destination', type=Path)
args = parser.parse_args()
if not args.source.is_file():
    parser.error('Banco de origem inexistente.')
if args.destination.exists():
    parser.error('Use um destino novo; backups existentes nao sao sobrescritos.')
args.destination.parent.mkdir(parents=True, exist_ok=True)
os.umask(0o077)
with closing(sqlite3.connect(args.source.resolve().as_uri() + '?mode=ro', uri=True)) as source:
    with closing(sqlite3.connect(args.destination)) as destination:
        source.backup(destination)
        integrity = destination.execute('PRAGMA integrity_check').fetchone()[0]
        if integrity != 'ok':
            raise RuntimeError('Falha na verificacao de integridade.')
print('Backup criado; integrity_check=ok')
