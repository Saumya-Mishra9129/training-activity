# -*- coding: utf-8 -*-
# Copyright (c) 2013,14 Walter Bender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, write to the Free Software
# Foundation, 51 Franklin Street, Suite 500 Boston, MA 02110-1335 USA

import os
import email.utils
import re
from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

import logging
_logger = logging.getLogger('training-activity-tasks')

from sugar3.graphics import style

from graphics import Graphics
from testutils import (get_nick, get_favorites, get_rtf, get_uitree_root,
                       find_string)


FONT_SIZES = ['xx-small', 'x-small', 'small', 'medium', 'large', 'x-large',
              'xx-large']


def get_task_list(task_master):
    return [[Intro1Task(task_master),
             Intro2Task(task_master),
             Intro3Task(task_master),
             ValidateEmailTask(task_master),
             BadgeOneTask(task_master)],
            [NickChange1Task(task_master),
             NickChange2Task(task_master),
             NickChange3Task(task_master),
             NickChange4Task(task_master),
             NickChange5Task(task_master),
             WriteSave1Task(task_master),
             WriteSave2Task(task_master),
             WriteSave3Task(task_master),
             WriteSave4Task(task_master),
             WriteSave5Task(task_master),
             BadgeTwoTask(task_master)],
            # [AddFavoriteTask(task_master),
            #  RemoveFavoriteTask(task_master),
            #  BadgeThreeTask(task_master)],
            [FinishedAllTasks(task_master)]]


class Task():
    ''' Generate class for defining tasks '''

    def __init__(self, task_master):
        self._name = 'Generic Task'
        self.uid = None
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def set_font_size(self, size):
        if size < len(FONT_SIZES):
            self._font_size = size

    def get_font_size(self):
        return self._font_size

    font_size = GObject.property(type=object, setter=set_font_size,
                                 getter=get_font_size)

    def set_zoom_level(self, level):
        self._zoom_level = level

    def get_zoom_level(self):
        return self._zoom_level

    zoom_level = GObject.property(type=object, setter=set_zoom_level,
                                 getter=get_zoom_level)

    def test(self, exercises, task_data):
        ''' The test to determine if task is completed '''
        raise NotImplementedError

    def after_button_press(self):
        ''' Anything special to do after the task is completed? '''
        return

    def get_success(self):
        ''' String to present to the user when task is completed '''
        return _('Success!')

    def get_retry(self):
        ''' String to present to the user when task is not completed '''
        return _('Keep trying')

    def get_data(self):
        ''' Any data needed for the test '''
        return None

    def get_pause_time(self):
        ''' How long should we pause between testing? '''
        return 5000

    def requires(self):
        ''' Return list of tasks (uids) required prior to completing this
            task '''
        return []

    def is_collectable(self):
        ''' Should this task's data be collected? '''
        return True

    def get_name(self):
        ''' String to present to the user to define the task '''
        raise NotImplementedError

    def get_help_info(self):
        ''' Is there help associated with this task? '''
        return (None, None)  # title, url (from Help.activity)

    def get_page_count(self):
        return 1

    def get_graphics(self, page=0):
        ''' Graphics to present with the task '''
        return None

    def is_completed(self):
        ''' Has this task been marked as complete? '''
        data = self._task_master.read_task_data(self.uid)
        if data is not None and 'completed' in data:
            return data['completed']
        return False


class Intro1Task(Task):

    def __init__(self, task_master):
        self._name = _('Intro One')
        self.uid = 'intro-task-1'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def get_name(self):
        return self._name

    def is_collectable(self):
        return False

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self):
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html', 'introduction1.html')
        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_("Let's go!"),
                                     self._task_master.task_button_cb)
        return graphics, button


class Intro2Task(Task):

    def __init__(self, task_master):
        self._name = _('Enter Name')
        self.uid = 'enter-name-task'
        self.entries = []
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        if len(self.entries) == 0:
            _logger.error('missing entry')
            return False
        if len(self.entries[0].get_text()) == 0:
            return False
        else:
            return True

    def after_button_press(self):
        self._task_master.write_task_data('name', self.entries[0].get_text())

    def get_name(self):
        return self._name

    def get_graphics(self):
        self.entries = []
        target = self._task_master.read_task_data('name')
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html',
                            'introduction2.html')

        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)
        if target is not None:
            self.entries.append(graphics.add_entry(text=target))
        else:
            self.entries.append(graphics.add_entry())
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class Intro3Task(Task):

    def __init__(self, task_master):
        self._name = _('Enter Email')
        self.uid = 'enter-email-task'
        self.entries = []
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def requires(self):
        return ['enter-name-task']

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        if len(self.entries) == 0:
            _logger.error('missing entry')
            return False
        entry = self.entries[0].get_text()
        if len(entry) == 0:
            return False
        realname, email_address = email.utils.parseaddr(entry)
        if email_address == '':
            return False
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email_address):
            return False
        return True

    def after_button_press(self):
        _logger.debug('Writing email address: %s' % self.entries[0].get_text())
        self._task_master.write_task_data('email_address',
                                       self.entries[0].get_text())

    def get_name(self):
        return self._name

    def get_graphics(self):
        self.entries = []
        name = self._task_master.read_task_data('name')
        if name is not None:
            name = name.split()[0]
        else:  # Should never happen
            _logger.error('missing name')
            name = ''
        email = self._task_master.read_task_data('email_address')
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html',
                            'introduction3.html?NAME=%s' % name)
        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)
        if email is not None:
            self.entries.append(graphics.add_entry(text=email))
        else:
            self.entries.append(graphics.add_entry())
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class ValidateEmailTask(Task):

    def __init__(self, task_master):
        self._name = _('Validate Email')
        self.uid = 'validate-email-task'
        self.entries = []
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def requires(self):
        return ['enter-email-task']

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        if len(self.entries) < 2:
            _logger.error('missing entry')
            return False
        entry0 = self.entries[0].get_text()
        entry1 = self.entries[1].get_text()
        if len(entry0) == 0 or len(entry1) == 0:
            return False
        if entry0 != entry1:
            return False
        realname, email_address = email.utils.parseaddr(entry0)
        if email_address == '':
            return False
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email_address):
            return False
        return True

    def after_button_press(self):
        self._task_master.write_task_data('email_address',
                                       self.entries[1].get_text())

    def get_name(self):
        return self._name

    def get_graphics(self):
        self.entries = []
        email = self._task_master.read_task_data('email_address')
        graphics = Graphics()
        if email is not None:
            self.entries.append(graphics.add_entry(text=email))
        else:  # Should never happen
            _logger.error('missing email address')
            self.entries.append(graphics.add_entry())
        graphics.add_text('\n\n')
        graphics.add_text(
            _('Please confirm that you typed your\n'
              'email address correctly by typing it again below.\n\n'),
            size=FONT_SIZES[self._font_size])
        self.entries.append(graphics.add_entry())
        graphics.add_text('\n\n')
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class BadgeOneTask(Task):

    def __init__(self, task_master):
        self._name = _('Badge One')
        self.uid = 'badge-one'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def requires(self):
        return ['enter-name-task', 'enter-email-task', 'validate-email-task']

    def is_collectable(self):
        return False

    def get_name(self):
        return self._name

    def get_pause_time(self):
        return 1000

    def after_button_press(self):
        target = self._task_master.read_task_data('name').split()[0]
        self._task_master.activity.add_badge(
            _('Congratulations %s!\n'
              "You’ve earned your first badge!" % target),
            icon='badge-intro')

    def test(self, exercises, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self):
        name = self._task_master.read_task_data('name')
        if name is not None:
            target = name.split()[0]
        else:
            target = ''
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html',
                            'introduction4.html?NAME=%s' % target)
        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Continue'),
                                     self._task_master.task_button_cb)
        return graphics, button


"""
class ChangeNickTask(Task):

    def __init__(self, task_master):
        self._name = _('Change Nick Task')
        self.uid = 'change-nick-task'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        if task_data['attempt'] == 0:
            _logger.debug('first attempt: saving nick value as %s' %
                          profile.get_nick_name())
            self._task_master.write_task_data('nick', profile.get_nick_name())
            return False
        else:
            target = self._task_master.read_task_data('nick')
            _logger.debug('%d attempt: comparing %s to %s' %
                          (task_data['attempt'], profile.get_nick_name(),
                           target))
            return not profile.get_nick_name() == target

    def after_button_press(self):
        return

    def get_name(self):
        return self._name

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_page_count(self):
        return 6

    def get_graphics(self, page=0):
        def button_callback(widget):
            from jarabe.model import shell
            _logger.debug('My turn button clicked')
            shell.get_model().set_zoom_level(shell.ShellModel.ZOOM_HOME)

        path = os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'images',
                            'home-view-menu.png')
        graphics = Graphics()
        button = None
        if page == 0:
            graphics.add_text(
                _('<b>Changing the Nickname</b>\n'
                  "In this lesson we’re going to learn how to change our\n"
                  'nickname on the XO.\n'
                  'You entered your nickname on the screen shown below\n'
                  'when you first started the XO up. Remember?\n\n'),
                size=FONT_SIZES[self._font_size])
        elif page == 1:
            graphics.add_image(path)
        elif page == 2:
            graphics.add_text(
                _('\n\n<b>What is the nickname?</b>\n'
                  'The nickname is your name on the XO, and will appear\n'
                  'all around Sugar as well as being visible on networks.\n\n'
                  'Watch the animation below to see how it’s done:\n\n'),
                size=FONT_SIZES[self._font_size])
        elif page == 3:
            graphics.add_image(path)
        elif page == 4:
            graphics.add_text(
                _('\n\n<b>Step-by-step:</b>\n'
                  '1. Go to the home screen\n'
                  '2. Right click on the central icon\n'
                  '3. Do other things\n'
                  '4. Type in a new nickname\n'
                  '5. Click yes to restart Sugar\n'
                  '6. Reopen the One Academy task_master to complete\n\n'),
                size=FONT_SIZES[self._font_size])
        elif page == 5:
            graphics.add_text(
                _('<b>Are you ready to try?</b>\n'
                  'Watch the animation again if you like.\n'
                  "When you’re ready to try, hit the \"My Turn\"\n"
                  'button below to go to the home screen.\n\n'),
                size=FONT_SIZES[self._font_size])
            graphics.add_button(_('My turn'), button_callback)
            graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'))
            button = graphics.add_button(_('Continue'),
                                         self._task_master.task_button_cb)
        return graphics, button
"""

class NickChange1Task(Task):

    def __init__(self, task_master):
        self._name = _('Nick Change Step One')
        self.uid = 'nick-change-task-1'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def is_collectable(self):
        return False

    def get_name(self):
        return self._name

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self):
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html', 'nickchange1.html')
        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class NickChange2Task(Task):

    def __init__(self, task_master):
        self._name = _('Nick Change Step Two')
        self.uid = 'nick-change-task-2'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def get_name(self):
        return self._name

    def is_collectable(self):
        return False

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self):
        graphics = Graphics()
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html', 'nickchange2.html')
        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class NickChange3Task(Task):

    def __init__(self, task_master):
        self._name = _('Nick Change Step Three')
        self.uid = 'nick-change-task-3'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def get_name(self):
        return self._name

    def is_collectable(self):
        return False

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self):
        graphics = Graphics()
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html', 'nickchange3.html')
        graphics = Graphics()
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class NickChange4Task(Task):

    def __init__(self, task_master):
        self._name = _('Nick Change Step Four')
        self.uid = 'nick-change-task-4'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def get_name(self):
        return self._name

    def get_pause_time(self):
        return 1000

    def test(self, exercises, task_data):
        if task_data['attempt'] == 0:
            _logger.debug('first attempt: saving nick value as %s' %
                          get_nick())
            self._task_master.write_task_data('nick', get_nick())
            return False
        else:
            return not get_nick() == self._task_master.read_task_data('nick')

    def get_graphics(self):

        def button_callback(widget):
            from jarabe.model import shell
            _logger.debug('My turn button clicked')
            shell.get_model().set_zoom_level(shell.ShellModel.ZOOM_HOME)

        offset = style.GRID_CELL_SIZE
        graphics = Graphics()
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html', 'nickchange4.html')
        graphics.add_uri('file://' + url, height=300)
        graphics.set_zoom_level(self._zoom_level)
        graphics.add_button(_('My turn'), button_callback)
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'))
        button = graphics.add_button(_('Continue'),
                                     self._task_master.task_button_cb)
        return graphics, button


class NickChange5Task(Task):

    def __init__(self, task_master):
        self._name = _('Nick Change Step Five')
        self.uid = 'nick-change-task-5'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def is_collectable(self):
        return False

    def requires(self):
        return ['nick-change-task-4']

    def test(self, exercises, task_data):
        return self._task_master.button_was_pressed

    def get_pause_time(self):
        return 1000

    def get_name(self):
        return self._name

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self):
        graphics = Graphics()
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html', 'nickchange5.html')
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)
        button = graphics.add_button(_('Continue'),
                                     self._task_master.task_button_cb)
        return graphics, button


class WriteSave1Task(Task):

    def __init__(self, task_master):
        self._name = _('Write Save Step One')
        self.uid = 'write-save-task-1'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def is_collectable(self):
        return False

    def test(self, exercises, task_data):
        return self._task_master.button_was_pressed

    def get_pause_time(self):
        return 1000

    def get_name(self):
        return self._name

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self):
        graphics = Graphics()
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html', 'writesave1.html')
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class WriteSave2Task(Task):

    def __init__(self, task_master):
        self._name = _('Write Save Step Two')
        self.uid = 'write-save-task-2'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def is_collectable(self):
        return False

    def test(self, exercises, task_data):
        return self._task_master.button_was_pressed

    def get_pause_time(self):
        return 1000

    def get_name(self):
        return self._name

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self):
        graphics = Graphics()
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html', 'writesave2.html')
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)
        button = graphics.add_button(_('Continue'),
                                     self._task_master.task_button_cb)
        return graphics, button


class WriteSave3Task(Task):

    def __init__(self, task_master):
        self._name = _('Write Save Step Three')
        self.uid = 'write-save-task-3'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def is_collectable(self):
        return False


    def test(self, exercises, task_data):
        return self._task_master.button_was_pressed

    def get_pause_time(self):
        return 1000

    def get_name(self):
        return self._name

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self):
        graphics = Graphics()
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html', 'writesave3.html')
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)
        button = graphics.add_button(_('Continue'),
                                     self._task_master.task_button_cb)
        return graphics, button


class WriteSave4Task(Task):

    def __init__(self, task_master):
        self._name = _('Write Save Step Four')
        self.uid = 'write-save-task-4'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def test(self, exercises, task_data):
        paths = get_rtf()
        for path in paths:
            # Check to see if there is a picture in the file
            if find_string(path, '\\pict'):
                return True
        return False

    def get_pause_time(self):
        return 1000

    def get_name(self):
        return self._name

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self):

        def button_callback(widget):
            from jarabe.model import shell
            shell.get_model().set_zoom_level(shell.ShellModel.ZOOM_HOME)

        graphics = Graphics()
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html', 'writesave4.html')
        graphics.add_uri('file://' + url, height=300)
        graphics.set_zoom_level(self._zoom_level)
        graphics.add_button(_('My turn'), button_callback)
        graphics.add_text(_('\n\nWhen you are done, you may continue.\n\n'))
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class WriteSave5Task(Task):

    def __init__(self, task_master):
        self._name = _('Write Save Step Five')
        self.uid = 'write-save-task-5'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def is_collectable(self):
        return False

    def requires(self):
        return ['write-save-task-4']

    def test(self, exercises, task_data):
        return self._task_master.button_was_pressed

    def get_pause_time(self):
        return 1000

    def get_name(self):
        return self._name

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self):
        graphics = Graphics()
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                            'Training.activity', 'html', 'writesave5.html')
        graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)
        button = graphics.add_button(_('Continue'),
                                     self._task_master.task_button_cb)
        return graphics, button


class BadgeTwoTask(Task):

    def __init__(self, task_master):
        self._name = _('Badge Two')
        self.uid = 'badge-two'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def requires(self):
        return ['nick-change-task-4', 'write-save-task-4']

    def is_collectable(self):
        return False

    def get_name(self):
        return self._name

    def get_pause_time(self):
        return 1000

    def after_button_press(self):
        target = self._task_master.read_task_data('name').split()[0]
        self._task_master.activity.add_badge(
            _('Congratulations %s!\n'
              "You’ve earned your second badge!" % target),
            icon='badge-intro')

    def test(self, exercises, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self):
        target = self._task_master.read_task_data('name').split()[0]
        graphics = Graphics()
        graphics.add_text(
            _('Congratulations %s!\n'
              "You’ve earned your second badge!\n\n" % target),
            bold=True,
            size=FONT_SIZES[self._font_size])
        graphics.add_icon('badge-intro')
        graphics.add_text(
            _('\n\nMost badges require you to complete multiple '
              'tasks.\n'
              'Press Continue to start on your next one!\n\n'),
            size=FONT_SIZES[self._font_size])
        button = graphics.add_button(_('Continue'),
                                     self._task_master.task_button_cb)
        return graphics, button


class AddFavoriteTask(Task):

    def __init__(self, task_master):
        self._name = _('Add Favorite Task')
        self.uid = 'add-favorites-task'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def test(self, exercises, task_data):
        if task_data['attempt'] == 0:
            favorites_list = get_favorites()
            self._task_master.write_task_data('favorites', len(favorites_list))
            return False
        else:
            favorites_count = len(get_favorites())
            saved_favorites_count = \
                self._task_master.read_task_data('favorites')
            return favorites_count > saved_favorites_count

    def get_name(self):
        return self._name

    def get_help_info(self):
        return ('Home', 'home_view.html')

    def get_graphics(self):
        path = os.path.join(os.path.expanduser('~'), 'Activities',
                            'Help.activity', 'images',
                            'Journal_main_annotated.png')
        graphics = Graphics()
        graphics.add_text(_('Try adding a favorite to your homeview.\n\n'),
                          size=FONT_SIZES[self._font_size])
        graphics.add_image(path)
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class RemoveFavoriteTask(Task):

    def __init__(self, task_master):
        self._name = _('Remove Favorite Task')
        self.uid = 'remove-favorites-task'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def test(self, exercises, task_data):
        if task_data['attempt'] == 0:
            favorites_list = get_favorites()
            self._task_master.write_task_data('favorites', len(favorites_list))
            return False
        else:
            favorites_count = len(get_favorites())
            saved_favorites_count = \
                self._task_master.read_task_data('favorites')
            return favorites_count < saved_favorites_count

    def get_name(self):
        return self._name

    def get_help_info(self):
        return ('Home', 'home_view.html')

    def get_graphics(self):
        path = os.path.join(os.path.expanduser('~'), 'Activities',
                            'Help.activity', 'images',
                            'Journal_main_annotated.png')
        graphics = Graphics()
        graphics.add_text(
            _('Now try removing a favorite to your homeview.\n\n'),
            size=FONT_SIZES[self._font_size])
        graphics.add_image(path)
        button = graphics.add_button(_('Next'),
                                     self._task_master.task_button_cb)
        return graphics, button


class BadgeThreeTask(Task):
    def __init__(self, task_master):
        self._name = _('Badge Three')
        self.uid = 'badge-3'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def requires(self):
        return ['add-favorites-task', 'remove-favorites-task']

    def is_collectable(self):
        return False

    def get_name(self):
        return self._name

    def get_pause_time(self):
        return 1000

    def after_button_press(self):
        target = self._task_master.read_task_data('name').split()[0]
        self._task_master.activity.add_badge(
            _('Congratulations %s!\n'
              "You’ve earned your third badge!" % target),
            icon='badge-intro')

    def test(self, exercises, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self):
        target = self._task_master.read_task_data('name').split()[0]
        graphics = Graphics()
        graphics.add_text(
            _('Congratulations %s!\n'
              "You’ve earned your third badge!\n\n" % target),
            bold=True, size=FONT_SIZES[self._font_size])
        graphics.add_icon('badge-intro')
        graphics.add_text(
            _('\n\nMost badges require you to complete multiple '
              'tasks.\n'
              'Press Continue to start on your next one!\n\n'),
            size=FONT_SIZES[self._font_size])
        button = graphics.add_button(_('Continue'),
                                     self._task_master.task_button_cb)
        return graphics, button


class FinishedAllTasks(Task):

    def __init__(self, task_master):
        self._name = _('Finished All Tasks')
        self.uid = 'finished'
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0

    def requires(self):
        return ['enter-name-task', 'enter-email-task', 'validate-email-task',
                'nick-change-task-4', 'write-save-task-4']

    def test(self, exercises, task_data):
        self._task_master.completed = True
        return True

    def get_name(self):
        return self._name

    def get_graphics(self):
        graphics = Graphics()
        graphics.add_text(_('You are a Sugar Zenmaster.\n\n'),
                          size=FONT_SIZES[self._font_size])
        button = graphics.add_button(_('Continue'),
                                     self._task_master.task_button_cb)
        return graphics, button


class UITest(Task):

    def __init__(self, task_master):
        self._name = _('UI Test Task')
        self.uid = 'uitest'
        self._task_master = task_master

    def test(self, exercises, task_data):
        return self._uitester()

    def _uitester(self):
        _logger.debug('uitree')
        uitree_root = get_uitree_root()
        _logger.debug(uitree_root)
        for node in uitree_root.get_children():
            _logger.debug('%s (%s)' % (node.name, node.role_name))
            for node1 in node.get_children():
                _logger.debug('> %s (%s)' % (node1.name, node1.role_name))
                for node2 in node1.get_children():
                    _logger.debug('> > %s (%s)' %
                                  (node2.name, node2.role_name))
        return True
