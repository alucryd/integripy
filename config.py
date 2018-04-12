from pathlib import Path

SRC_ROOT = Path.home()
DST_ROOT = Path('/mnt')
ROOT_DIRECTORIES = ('Music', 'Videos')
BLACKLIST = ('$RECYCLE.BIN',)
EXTENSIONS = ('.flac', '.m4a', '.mkv', '.mp3', '.mp4')
CHUNK_SIZE = 8096

SMTP_HOST = '127.0.0.1'
SMTP_PORT = 587
SMTP_LOGIN = ''
SMTP_PASSWORD = ''

MAIL_FROM = ''
MAIL_TO = ''
