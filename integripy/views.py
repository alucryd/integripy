import os
from pathlib import Path

from flask import render_template, request, jsonify

from integripy.explorer import Explorer, Directory, File
from integripy import application


@application.route('/')
def index():
    return render_template('index.html')


@application.route("/explorer", methods=['POST'])
def explorer():
    """Returns information about the path and its children."""
    root = application.config['SRC_ROOT'] if request.json.get('src') else application.config['DST_ROOT']
    path = Path(request.json.get('path'))
    full_path = root / path
    statvfs = os.statvfs(full_path)
    items = [Explorer.item(root, c.relative_to(root)) for c in full_path.iterdir() if
             not c.name.startswith('.') and c.name not in application.config['BLACKLIST']]
    children = [{
        'name': '.',
        'path': str(path),
        'directory': True,
        'corrupt': False,
        'computing': False,
        'selected': False
    }]
    if full_path == root:
        # Only list select directories in the root
        items = [item for item in items if item.name in application.config['ROOT_DIRECTORIES']]
    else:
        # Only list select files everywhere else
        items = [item for item in items if
                 item.full_path.is_dir() or item.path.suffix in application.config['EXTENSIONS']]
        children.append({
            'name': '..',
            'path': str(path.parent),
            'directory': True,
            'corrupt': False,
            'computing': False,
            'selected': False
        })
    children += [
        {
            'name': item.name,
            'directory': isinstance(item, Directory),
            'path': str(item.path),
            'src_size': 0,
            'dst_size': 0,
            'clean_hash': item.clean_hash,
            'corrupt': False,
            'computing': False,
            'selected': False
        }
        for item in items
    ]
    children.sort(key=lambda child: (not child['directory'], child['name']))
    return jsonify({
        'path': str(path),
        'total_size': statvfs.f_blocks * statvfs.f_frsize,
        'free_size': statvfs.f_bfree * statvfs.f_frsize,
        'parts': ['~'] + list(path.parts),
        'children': children
    })


@application.route("/directory_size", methods=['POST'])
def directory_size():
    """Returns the sum of all the file sizes in the directory tree."""
    path = Path(request.json.get('path'))
    return jsonify({
        'src_size': Directory(application.config['SRC_ROOT'], path).size,
        'dst_size': Directory(application.config['DST_ROOT'], path).size
    })


@application.route("/file_size", methods=['POST'])
def file_size():
    """Returns the size of the file."""
    path = Path(request.json.get('path'))
    meta_file = Explorer.meta_file(path)
    return jsonify({
        'src_size': meta_file.src_file.size if meta_file.src_file is not None else 0,
        'dst_size': meta_file.dst_file.size if meta_file.dst_file is not None else 0
    })


@application.route("/transfer", methods=['POST'])
def transfer():
    """Transfers the source file(s) to the destination rsync-like."""
    root = application.config['SRC_ROOT'] if request.json.get('src') else application.config['DST_ROOT']
    path = Path(request.json.get('path'))
    item = Explorer.item(root, path)
    paths = []
    if isinstance(item, Directory):
        paths += [file.path for file in item.files_recursive()]
    else:
        paths.append(path)
    for path in paths:
        meta_file = Explorer.meta_file(path)
        src = meta_file.src_file if root == application.config['SRC_ROOT'] else meta_file.dst_file
        dst = meta_file.dst_file if root == application.config['SRC_ROOT'] else meta_file.src_file
        if dst is None:
            dst = src.mirror()
        if src.hash != dst.hash:
            Explorer.sync(src, dst)
        dst.update_hash_file()
    return ''


@application.route("/check_integrity", methods=['POST'])
def check_integrity():
    """Checks the current hash against the hash file."""
    root = application.config['SRC_ROOT'] if request.json.get('src') else application.config['DST_ROOT']
    path = Path(request.json.get('path'))
    item = Explorer.item(root, path)
    return jsonify(item.corrupt) if isinstance(item, File) else jsonify(False)


@application.route("/update_hash_file", methods=['POST'])
def update_hash_file():
    """Updates the hash file."""
    root = application.config['SRC_ROOT'] if request.json.get('src') else application.config['DST_ROOT']
    path = Path(request.json.get('path'))
    item = Explorer.item(root, path)
    if isinstance(item, File):
        item.update_hash_file()
    return item.clean_hash
