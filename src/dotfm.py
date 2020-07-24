#!/usr/bin/env python3

#==========================
# dotfm - dot file manager
#==========================
# authors: gearsix
# created: 2020-01-15
# updated: 2020-07-20
# notes:

#---------
# IMPORTS
#---------
import sys
import os
import csv
import logging
import argparse

#---------
# GLOBALS
#---------
NAME = os.path.basename(__file__)       # program name
USER = os.getenv('USER')                # $USER calling dotfm
ARGS = sys.argv                         # parsed arguments
EDITOR = os.getenv('EDITOR') or 'nano'  # text editor to modify dotfiles with
VERSION = 'v1.0.2'
DOTFM_CSV_FILE = '/home/{}/.config/dotfm/dotfm.csv'.format(USER)
KNOWN_DOTFILES = [ # dotfiles that dotfm knows by default
    # location                                          # aliases
    ['/home/{}/.config/dotfm/dotfm.csv'.format(USER),   'dotfm.csv', 'dotfm'],
    ['/home/{}/.bashrc'.format(USER),                   '.bashrc', 'bashrc'],
    ['/home/{}/.profile'.format(USER),                  '.profile', 'profile'],
    ['/home/{}/.bash_profile'.format(USER),             '.bash_profile', 'bash_profile'],
    ['/home/{}/.ssh/config'.format(USER),               'ssh_config'],
    ['/home/{}/.vimrc'.format(USER),                    '.vimrc', 'vimrc'],
    ['/home/{}/.config/nvim/init.vim'.format(USER),     'init.vim', 'nvimrc'],
    ['/home/{}/.tmux.conf'.format(USER),                'tmux.conf', 'tmux.conf'],
    ['/home/{}/.config/rc.conf'.format(USER),           'rc.conf', 'ranger.conf'],
    ['/home/{}/.config/user-dirs.dirs'.format(USER),    'user-dirs.dirs', 'xdg-user-dirs'],
]

#-----------
# FUNCTIONS
#-----------
def error_exit(message):
    LOGGER.error(message)
    sys.exit()

def parse_arguments():
    global ARGS
    valid_commands = ['install', 'remove', 'edit', 'install-all', 'list']
    
    parser = argparse.ArgumentParser(description='a simple tool to help you manage your dot files, see \"man dotfm\" for more.')
    parser.add_argument('cmd', metavar='COMMAND', choices=valid_commands, help='the dotfm COMMAND to execute: {}'.format(valid_commands))
    parser.add_argument('dotfile', metavar='DOTFILE', help='the target dotfile to execute COMMAND on')
    parser.add_argument('-d', '--debug', action='store_true', help='display debug logs')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(VERSION))
    ARGS = parser.parse_args()

def validate_dotfile_path(dotfile, dotfile_path):
    if not os.path.exists(dotfile_path):
        error_exit('DOTFILE \"{}\" ({}) not found'.format(dotfile, dotfile_path))
    if not os.path.isfile(dotfile_path):
        error_exit('DOTFILE \"{}\" ({}) should be a file, not a dir'.format(dotfile, dotfile_path))

def validate_dotfiledir_path(dirname, dotfiledir_path):
    if not os.path.exists(dotfiledir_path):
        error_exist('DOTFILE DIRECTORY \"{}\" ({}) not found'.format(dotfile, dotfiledir_path))
    if not os.path.isdir(dotfiledir_path):
        error_exit('DOTFILE DIRECTORY \"{}\" ({}) is not a directory'.format(dotfile, dotfiledir_path))

def dotfm_init():
    LOGGER.info('loading dotfile locations...')

    if not os.path.exists(DOTFM_CSV_FILE):
        LOGGER.warning('dotfile_locations not found')

        # get location to create dotfm.csv at
        location = input('where would you like to store the dotfm config (default: {})? '.format(DOTFM_CSV_FILE))
        if len(location) > 0:
            if os.path.exists(location):
                yn = ''
                while yn == '':
                    yn = input('{} already exists, overwrite (y/n)? '.format(location))
                    if yn[0] == 'y':
                        LOGGER.info('overwriting {}'.format(location))
                    elif yn[0] == 'n':
                        LOGGER.info('{} already exists, using default location ({})'.format(DOTFILE_LOCATION))
                        location = DOTFM_CSV_FILE
                    else:
                        yn = ''
        else: # use default
            location = DOTFM_CSV_FILE

        # write dotfm dotfile to csv
        dotfm_csv = open(location, "w")
        dfl = KNOWN_DOTFILES[0][0]
        for i, alias in enumerate(KNOWN_DOTFILES[0]):
            if i == 0:
                continue # 0 = the location (not alias)
            dfl += ',{}'.format(alias)
        dotfm_csv.write(dfl+'\n')
        dotfm_csv.close()

        # create dotfm.csv symbolic link
        os.system('mkdir -p {}'.format(os.path.dirname(DOTFM_CSV_FILE)))
        os.system('ln -fsv {} {}'.format(os.path.abspath(location), DOTFM_CSV_FILE))

def dotfm_install(dotfile):
    LOGGER.info('installing {}...'.format(dotfile))
    
    found = False
    for dfl in DOTFILE_LOCATIONS:
        if found == True:
            break
        for name in dfl[0]:
            if os.path.basename(dotfile) == name:
                found = True
                dest = os.path.abspath(dfl[1])
                # make sure path exists
                if not os.path.exists(os.path.dirname(dest)):
                    os.system('mkdir -vp {}'.format(dest))
                # check if file already exists
                if os.path.lexists(dest):
                    LOGGER.warning('{} already exists!'.format(dest))
                    oca = ''
                    while oca == '':
                        oca = input('[o]verwrite/[c]ompare/[a]bort? ')
                        if len(oca) > 0:
                            if oca[0] == 'o':
                                LOGGER.info('overwriting {} with {}'.format(dest, dotfile))
                                LOGGER.info('backup {} -> {}.bak'.format(dest, dest))
                                os.system('mv {} {}.bak'.format(dest, dest))
                                LOGGER.info('linking {} -> {}'.format(dest, dotfile)) 
                                os.system('ln -s {} {}'.format(dotfile, dest))
                            elif oca[0] == 'c':
                                LOGGER.info('comparing {} to {}'.format(dotfile, dest))
                                os.system('diff -y {} {}'.format(dotfile, dest))  # maybe use vimdiff
                                oca = ''
                            elif oca[0] == 'a':
                                LOGGER.info('aborting install')
                                sys.exit()
                            else:
                                oca = ''
                        else:
                            oca = ''
                else:
                    os.system('ln -vs {} {}'.format(dotfile, dest))
                break

    # check for unrecognised dotfile
    if found == False:
        error_exit('dotfile basename not recognised ({})!\nmake sure that the dotfile name and location to install to exist in \"DOTFILE_LOCATIONS\" (see src/dotfm.py)'.format(os.path.basename(dotfile)))
    else:
        LOGGER.info('success - you might need to re-open the terminal to see changes take effect')

def dotfm_installall(dotfile_dir):
    LOGGER.info('installing all dotfiles in {}'.format(dotfile_dir))

    for df in os.listdir(os.path.abspath(dotfile_dir)):
        df = os.path.abspath('{}/{}'.format(dotfile_dir, df))
        if os.path.isfile(df):
            LOGGER.debug('found {}, installing...'.format(df))
            found = False
            for dfl in DOTFILE_LOCATIONS:
                if os.path.basename(df) in dfl[0]:
                    found = True
            if found:
                dotfm_install(df)
            else:
                LOGGER.info('found {}, skipping...'.format(df))
        elif os.path.isdir(df) and os.path.basename(df) != ".git":
            LOGGER.debug('found dir {}')
            dotfm_installall(df)

def dotfm_remove(dotfile):
    LOGGER.info('removing {}...'.format(dotfile))

    found = False
    for dfl in DOTFILE_LOCATIONS:
        if found == True:
            break
        for name in dfl[0]:
            if os.path.basename(dotfile) == name:
                found = True
                target = '{}'.format(os.path.abspath(dfl[1]), name)
                os.system('rm -v {}'.format(target))
                break

def dotfm_edit(dotfile):
    LOGGER.info('editing {}...'.format(dotfile))

    found = False
    target = ''
    for dfl in DOTFILE_LOCATIONS:
        if found == True:
            break
        for name in dfl[0]:
            if os.path.basename(dotfile) == name:
                found = True
                target = '{}'.format(os.path.abspath(dfl[1]))
                os.system('{} {}'.format(EDITOR, target))
                LOGGER.info('success - you might need to re-open the terminal to see changes take effect')
                break

    if target == '':
        error_exit('could not find {} in DOTFILE_LOCATIONS'.format(os.path.basename(dotfile)))

def dotfm_list(dotfile):
    LOGGER.info('listing dotfm files')

    found = False
    dotfm_csv = open(DOTFM_CSV_FILE, "r")
    dotfm_csv_reader = csv.reader(dotfm_csv)
    LOGGER.info('\t{} Location'.format('Aliases...'.ljust(35)))
    for dfl in dotfm_csv_reader:
        # list all dotfile locations
        if dotfile == 'all':
            dfln = '"' + '", "'.join(dfl[1:]) + '"'
            LOGGER.info('\t{} {} -> {}'.format(dfln.ljust(35), dfl[0], os.path.realpath(dfl[0])))
        # list specific dotfile location
        else:
            if found == True:
                break
            for name in dfl:
                if dotfile == name:
                    found = True
                    dfln = '"' + '", "'.join(dfl[1:]) + '"'
                    LOGGER.info('\t{} {} -> {}'.format(dfln.ljust(35), dfl[0], os.path.realpath(dfl[0])))
                    break

#------
# MAIN
#------
if __name__ == '__main__':
    # parse args
    parse_arguments()
    command = ARGS.cmd
    dotfile = ARGS.dotfile

    # init LOGGER
    if ARGS.debug == True:
        logging.basicConfig(level=logging.DEBUG, format='%(lineno)-4s {} | %(asctime)s | %(levelname)-7s | %(message)s'.format(NAME))
        LOGGER = logging.getLogger(__name__)
        LOGGER.debug('displaying debug logs')
    else:
        logging.basicConfig(level=logging.INFO, format='%(lineno)-4s {} | %(asctime)s | %(levelname)-7s | %(message)s'.format(NAME))
        LOGGER = logging.getLogger(__name__)

    # load dotfile locations
    dotfm_init()

    # run command
    if command == 'install':
        validate_dotfile_path(dotfile, os.path.abspath(dotfile))
        dotfm_install(os.path.abspath(dotfile))
    elif command == 'remove':
        validate_dotfile_path(dotfile)
        dotfm_remove(os.path.abspath(dotfile))
    elif command == 'edit':
        dotfm_edit(os.path.abspath(dotfile))
    elif command == 'install-all':
        validate_dotfiledir_path(dotfile, os.path.abspath(dotfile))
        dotfm_installall(os.path.abspath(dotfile))
    elif command == 'list':
        dotfm_list(dotfile)

