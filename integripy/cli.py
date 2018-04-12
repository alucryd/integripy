import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from time import perf_counter

import click
import humanize

from integripy import application
from integripy.explorer import Directory


def _sendmail(subject: str, text: str) -> None:
    msg = MIMEText(text)
    msg['Subject'] = subject
    msg['From'] = application.config['MAIL_FROM']
    msg['To'] = application.config['MAIL_TO']
    s = smtplib.SMTP(application.config['SMTP_HOST'], application.config['SMTP_PORT'])
    s.ehlo()
    s.starttls()
    s.login(application.config['SMTP_LOGIN'], application.config['SMTP_PASSWORD'])
    s.send_message(msg)
    s.quit()


@application.cli.command()
def generate_new_hashes():
    """Generates hash files for all new files."""
    start = perf_counter()
    paths = []
    count = 0
    for directory in application.config['DIRECTORIES']:
        for file in Directory(application.config['SRC_ROOT'], Path(directory)).files_recursive():
            if not file.clean_hash:
                count += 1
                click.echo(f'Analyzing {file.path}')
                file.update_hash_file()
                paths.append(str(file.path))
    end = perf_counter()
    time = humanize.naturaldelta(end - start)
    text = '\n'.join(paths)
    text += '\n\n'
    text += f'Analyzed {count} files in {time}.'
    _sendmail('New files', text)


@application.cli.command()
def verify_all_hashes():
    """Verify hash files for all files."""
    start = perf_counter()
    paths = []
    count = 0
    for directory in application.config['DIRECTORIES']:
        for file in Directory(application.config['SRC_ROOT'], Path(directory)).files_recursive():
            count += 1
            click.echo(f'Analyzing {file.path}')
            if file.corrupt:
                paths.append(str(file.path))
    end = perf_counter()
    time = humanize.naturaldelta(end - start)
    text = '\n'.join(paths)
    text += '\n\n'
    text += f'Analyzed {count} files in {time}.'
    _sendmail('Corrupt files', text)
