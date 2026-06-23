#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import time
import json
import logging
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

REPO = Path(__file__).resolve().parents[1]
SITE = REPO / 'site'
PID_FILE = REPO / '.watch.pid'
LOG_FILE = REPO / '.watch.log'
BUILD = str(REPO / 'builder' / 'build.py')
WATCH_PATHS = [
    SITE / 'article.html',
    SITE / 'article-review.html',
    SITE / 'article-howto.html',
    SITE / 'articles.html',
    SITE / 'rankings.html',
    SITE / 'tags.html',
    SITE / 'index.html',
    SITE / 'about.html',
    SITE / 'contact.html',
    SITE / 'policy.html',
    SITE / 'disclaimer.html',
    SITE / '404.html',
    SITE / '特商法.html',
    SITE / 'search-index.json',
    SITE / 'tag',
    SITE / 'builder',
]

logging.basicConfig(level=logging.INFO, format='%(asctime)s [watch] %(message)s', handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8')])
log = logging.getLogger('watch')
_debounce = 0.0


class RebuildHandler(FileSystemEventHandler):
    def on_modified(self, event):
        global _debounce
        if event.is_directory:
            return
        p = Path(event.src_path)
        if not any(str(p).endswith(ext) for ext in {'.html', '.json', '.md'}):
            return
        now = time.time()
        if now < _debounce:
            return
        _debounce = now + 1.2
        log.info('changed: %s', p.name)
        try:
            r = subprocess.run([sys.executable, BUILD], capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                log.info('rebuild OK')
            else:
                log.error('rebuild failed: %s', (r.stderr or '')[-500:])
        except Exception as e:
            log.error('rebuild error: %s', e)


def start():
    observer = Observer()
    watched = set()
    for p in WATCH_PATHS:
        target = p if p.is_dir() else p.parent
        if target.exists() and target not in watched:
            observer.schedule(RebuildHandler(), str(target), recursive=False)
            watched.add(target)
    observer.start()
    PID_FILE.write_text(str(os.getpid()), encoding='utf-8')
    log.info('started pid=%s dirs=%s', os.getpid(), len(watched))
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    PID_FILE.unlink(missing_ok=True)
    log.info('stopped')


if __name__ == '__main__':
    start()
