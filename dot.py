#!/usr/bin/python
# -*- coding:utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
import os, sys
from os.path import join, isfile, isdir


def option(command, default='__special_none__', mode=str):
    """Decorator to pass sys.argv to functions,  
    imitates https://github.com/pallets/click
    """
    if type(mode) != type:
        raise ValueError('mode must be type')
    def decorate(fn):
        def wrapper(*args):
            opt = default
            if command in sys.argv:
                li = []
                for i in sys.argv[sys.argv.index(command) + 1:]:
                    if i.find('-') == 0:
                        break
                    li.append(i)
                if mode == tuple:
                    opt = tuple(li)
                elif len(li) > 0:
                    if mode == bool:
                        opt = True
                    else:
                        opt = mode(li[0])
                elif default == '__special_none__':
                    print('Missing value for %s.' % command)
                    sys.exit(-2)
            elif dafault == '__special_none__':
                print("Missing option '%s'" % command)
                sys.exit(-1)
            return fn(*args + (opt,))
        return wrapper
    return decorate


help_text = """DOT:
    Naive dotfiles management util by geneLocated

usage:
    `make <command> [args=<args>]` or
    `python {fn} <command> <args>`

commands:
    help:		Display this message
    list:		List exist topics
    list <topic>:	List .files under this topic
    apply <topic>:	Apply a topic of .files (by making soft links in some directory)
    recover <topic>:	Stop manage a topic of .files, and try to restore

    add <file> ...:	Stage files you want to backup in buffer
    status:		Display files you staged and the topic you are going to commit to
    commit <topic>: 	Store buffer data to a topic

operation flow:
    to get files into management:
        [{fn} add] -> ... -> [{fn} add] -> [{fn} commit] -> [{fn} apply] -> [git add .] -> [git commit]
    to continue managing:
        [{fn} apply]""".format(fn=sys.argv[0])


def help_():
    print(help_text)


@option('list', default=None)
def list_(topic=None):
    if topic == None:
        # list topics in this repo
        print(_gettopic())
    else:
        # list dotfiles under a topic
        print(_getfiles(_prefixtopic(topic)))


# os.path.join('/opt/someplace', '/home/user/') returns the latter
def _rmrootslash(dir_):
    """Remove root slash"""
    if dir_[0] == '/':
        return dir_[1:]
    return dir_


def _prefixtopic(topic):
    """Prefix with 'topic.' if not given"""
    return topic if topic.find('topic.') != -1 \
        else 'topic.' + topic


def _gettopic():
    file_and_dir = os.listdir('.')
    dironly = [i for i in file_and_dir
               if isdir(join('.', i))]
    topics = [i[len('topic.'):] for i in dironly if i.find('topic.') == 0]
    return topics


def _getfiles(topic):
    os.chdir(join('.', topic))
    dirs = os.walk('.')
    # os.walk returns a list of tuples,
    # every tuple is (root: str, dirs: list, files: list)
    # files = [f for i in dirs for f in i[2]]
    files = [join(i[0], f)[1:] for i in dirs for f in i[2]]
    os.chdir('..')
    return files


@option('apply')
def apply(topic):
    """Apply a topic."""
    topic = _prefixtopic(topic)
    for target in _getfiles(topic):
        ori = join(os.getcwd(), topic, _rmrootslash(target))
        target = _rpenv(target)
        print(ori)
        print('\033[1;32m{}\033[0m'.format(target))
        # make dir if not exist
        dir_ = _getdir(target)
        if not isdir(dir_):
            os.makedirs(dir_)
        # backup the file if already exist
        if isfile(target) and not isfile(target + '.BAK'):
            os.rename(target, target + '.BAK')
        else:
            try:
                os.remove(target)
            # except FileNotFoundError:
            except OSError:
                pass
        os.system('ln -s {ori} {tar}'.format(ori="'{}'".format(ori), tar=target))


@option('recover')
def recover(topic):
    """Remove the link file, and recover from the .BAK file"""
    topic = _prefixtopic(topic)
    for f in _getfiles(topic):
        f = _rpenv(f)
        if isfile(f):
            os.remove(f)
        if isfile(f + '.BAK'):
            os.rename(f + '.BAK', f)


def _getdir(fullname):
    """Get dir of a file"""
    return os.path.split(fullname)[0]


def _getshortname(fullname):
    """Get short name of a file"""
    return os.path.split(fullname)[1]


def _rpenv(string):
    """Replace env var with its value."""
    import re
    found = re.findall('\\${.*?}', string)
    if len(found) == 0:
        return string
    fn_value = string  # /home/user/.vimrc
    # bracketed environment variable
    for bkt_var in found:
        var = bkt_var[2:-1]  # remove ${}
        if var in os.environ:
            fn_value = fn_value.replace(bkt_var, os.environ[var])
        else:
            raise ValueError(
                'environment variable `${}` not exist'.format(bkt_var))
        return fn_value


@option('add', mode=tuple)
def add(files):
    """Add file(s) into buffer."""
    from shutil import copy
    if len(files) == 0:
        print('Nothing specified, nothing added.')
    else:
        for arg in files:
            before = _rpenv(arg)
            before = os.path.abspath(before)
            after = arg
            # add relative file to abs path BUFFER
            if not os.path.isabs(_rpenv(arg)):
                after = os.path.abspath(arg)
            after = _getdir(join('BUFFER', _rmrootslash(after)))
            if not isdir(after):
                os.makedirs(after)
            copy(before, after)


def status():
    if isdir('BUFFER') and len(_getfiles('BUFFER')) != 0:
            print('Files staged in the buffer:')
            print(_getfiles('BUFFER'))
    else:
        print('Nothing in the buffer.')


@option('commit')
def commit(topic):
    """Store the files in the buffer to a topic."""
    if not (isdir('BUFFER') and len(_getfiles('BUFFER')) != 0):
        print('Fatal: no file staged in the buffer')
        print('  (use `{} add <file> ...` to stage files)'.format(sys.argv[0]))
    else:
        from shutil import move
        move('BUFFER', _prefixtopic(topic))


if __name__ == '__main__':
    # print(sys.argv)
    # display help if no args provided
    if len(sys.argv) < 2:
        help_()
    else:
        {'help': help_,
         'list': list_,
         'apply': apply,
         'recover': recover,
         'add': add,
         'status': status,
         'commit': commit}[sys.argv[1]]()
