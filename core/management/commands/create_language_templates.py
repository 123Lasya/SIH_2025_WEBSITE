import os
from pathlib import Path
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create _te and _hi copies of templates in farmers, buyers and panel'

    def handle(self, *args, **options):
        base = Path(__file__).resolve().parents[3] / 'templates'

        folders = ['farmers', 'buyers', 'panel']

        created = 0
        for f in folders:
            folder = base / f
            if not folder.exists():
                self.stdout.write(self.style.WARNING(f"Templates folder not found: {folder}"))
                continue

            for p in folder.glob('*.html'):
                text = p.read_text(encoding='utf-8')
                te = p.with_name(p.stem + '_te.html')
                hi = p.with_name(p.stem + '_hi.html')
                if not te.exists():
                    te.write_text(text, encoding='utf-8')
                    created += 1
                if not hi.exists():
                    hi.write_text(text, encoding='utf-8')
                    created += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created} language template files (if missing)."))
