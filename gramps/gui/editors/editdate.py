#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2006  Donald N. Allingham
# Copyright (C) 2009       Douglas S. Blank
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id$

"""
Date editing module for Gramps. 

The EditDate provides visual feedback to the user via a pixamp
to indicate if the associated GtkEntry box contains a valid date. Green
means complete and regular date. Yellow means a valid, but not a regular date.
Red means that the date is not valid, and will be viewed as a text string
instead of a date.

The DateEditor provides a dialog in which the date can be 
unambiguously built using UI controls such as menus and spin buttons.
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------


#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
__LOG = logging.getLogger(".EditDate")

#-------------------------------------------------------------------------
#
# GNOME modules
#
#-------------------------------------------------------------------------
from gi.repository import Gtk

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.sgettext
from gramps.gen.lib.date import Date, DateError
from gramps.gen.datehandler import displayer
from gramps.gen.const import URL_MANUAL_PAGE
from ..display import display_help
from ..managedwindow import ManagedWindow
from ..glade import Glade

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
MOD_TEXT = ( 
    (Date.MOD_NONE       , _('Regular')),
    (Date.MOD_BEFORE     , _('Before')),
    (Date.MOD_AFTER      , _('After')),
    (Date.MOD_ABOUT      , _('About')),
    (Date.MOD_RANGE      , _('Range')),
    (Date.MOD_SPAN       , _('Span')),
    (Date.MOD_TEXTONLY   , _('Text only')) )

QUAL_TEXT = (
    (Date.QUAL_NONE,       _('Regular')), 
    (Date.QUAL_ESTIMATED,  _('Estimated')), 
    (Date.QUAL_CALCULATED, _('Calculated')) )

CAL_TO_MONTHS_NAMES = {
    Date.CAL_GREGORIAN  : displayer.short_months,
    Date.CAL_JULIAN     : displayer.short_months,
    Date.CAL_HEBREW     : displayer.hebrew,
    Date.CAL_FRENCH     : displayer.french,
    Date.CAL_PERSIAN    : displayer.persian,
    Date.CAL_ISLAMIC    : displayer.islamic,
    Date.CAL_SWEDISH    : displayer.swedish }

WIKI_HELP_PAGE = '%s_-_Entering_and_Editing_Data:_Detailed_-_part_1' % URL_MANUAL_PAGE
WIKI_HELP_SEC = _('manual|Editing_Dates')

#-------------------------------------------------------------------------
#
# EditDate
#
#-------------------------------------------------------------------------
class EditDate(ManagedWindow):
    """
    Dialog allowing to build the date precisely, to correct possible 
    limitations of parsing and/or underlying structure of :class:`.Date`.
    """

    def __init__(self, date, uistate, track):
        """
        Initiate and display the dialog.
        """
        ManagedWindow.__init__(self, uistate, track, self)
        
        # Create self.date as a copy of the given Date object.
        self.date = Date(date)
        
        self.top = Glade()

        self.set_window(
            self.top.toplevel,
            self.top.get_object('title'),
            _('Date selection'))            
            
        self.calendar_box = self.top.get_object('calendar_box')
        for name in Date.ui_calendar_names:
            self.calendar_box.get_model().append([name])

        self.calendar_box.set_active(self.date.get_calendar())
        self.calendar_box.connect('changed', self.switch_calendar)

        self.quality_box = self.top.get_object('quality_box')
        for item_number in range(len(QUAL_TEXT)):
            self.quality_box.append_text(QUAL_TEXT[item_number][1])
            if self.date.get_quality() == QUAL_TEXT[item_number][0]:
                self.quality_box.set_active(item_number)

        self.type_box = self.top.get_object('type_box')
        for item_number in range(len(MOD_TEXT)):
            self.type_box.append_text(MOD_TEXT[item_number][1])
            if self.date.get_modifier() == MOD_TEXT[item_number][0]:
                self.type_box.set_active(item_number)
        self.type_box.connect('changed', self.switch_type)

        self.start_month_box = self.top.get_object('start_month_box')
        self.stop_month_box = self.top.get_object('stop_month_box')
        month_names = CAL_TO_MONTHS_NAMES[self.date.get_calendar()]
        for name in month_names:
            self.start_month_box.append_text(name)
            self.stop_month_box.append_text(name)
        self.start_month_box.set_active(self.date.get_month())
        self.stop_month_box.set_active(self.date.get_stop_month())
        
        self.start_day = self.top.get_object('start_day')
        self.start_day.set_value(self.date.get_day())
        self.start_year = self.top.get_object('start_year')
        self.start_year.set_value(self.date.get_year())

        self.stop_day = self.top.get_object('stop_day')
        self.stop_day.set_value(self.date.get_stop_day())
        self.stop_year = self.top.get_object('stop_year')
        self.stop_year.set_value(self.date.get_stop_year())
        
        self.dual_dated = self.top.get_object('dualdated')
        self.new_year = self.top.get_object('newyear')
        self.new_year.set_text(self.date.newyear_to_str())

        # Disable second date controls if not compound date
        if not self.date.is_compound():
            self.stop_day.set_sensitive(0)
            self.stop_month_box.set_sensitive(0)
            self.stop_year.set_sensitive(0)

        # Disable the rest of controls if a text-only date
        if self.date.get_modifier() == Date.MOD_TEXTONLY:
            self.start_day.set_sensitive(0)
            self.start_month_box.set_sensitive(0)
            self.start_year.set_sensitive(0)
            self.calendar_box.set_sensitive(0)
            self.quality_box.set_sensitive(0)
            self.dual_dated.set_sensitive(0)
            self.new_year.set_sensitive(0)

        self.text_entry = self.top.get_object('date_text_entry')
        self.text_entry.set_text(self.date.get_text())

        if self.date.get_slash():
            self.dual_dated.set_active(1)
            self.calendar_box.set_sensitive(0)
            self.calendar_box.set_active(Date.CAL_JULIAN)
        self.dual_dated.connect('toggled', self.switch_dual_dated)

        # The dialog is modal -- since dates don't have names, we don't
        # want to have several open dialogs, since then the user will
        # loose track of which is which. Much like opening files.
        
        self.return_date = None

        self.show()

        while True:
            response = self.window.run()
            if response == Gtk.ResponseType.HELP:
                display_help(webpage=WIKI_HELP_PAGE,
                                   section=WIKI_HELP_SEC)
            elif response == Gtk.ResponseType.DELETE_EVENT:
                break
            else:
                if response == Gtk.ResponseType.OK:
                    (the_quality, the_modifier, the_calendar, the_value, 
                     the_text, the_newyear) = self.build_date_from_ui()
                    self.return_date = Date(self.date)
                    try:
                        self.return_date.set(
                            quality=the_quality,
                            modifier=the_modifier,
                            calendar=the_calendar,
                            value=the_value,
                            text=the_text,
                            newyear=the_newyear)
                    except DateError: 
                        # Switch to text only mode, leave the dialog open
                        # so the user sees the old data. 
                        self.type_box.set_active(len(MOD_TEXT)-1)
                        continue
                self.close()
                break

    def build_menu_names(self, obj):
        """
        Define the menu entry for the :class:`.ManagedWindow`
        """
        return (_("Date selection"), None)

    def build_date_from_ui(self):
        """
        Collect information from the UI controls and return 
        5-tuple of (quality,modifier,calendar,value,text) 
        """
        # It is important to not set date based on these controls. 
        # For example, changing the caledar makes the date inconsistent
        # until the callback of the calendar menu is finished. 
        # We need to be able to use this function from that callback,
        # so here we just report on the state of all widgets, without
        # actually modifying the date yet.
        modifier = MOD_TEXT[self.type_box.get_active()][0]
        text = self.text_entry.get_text()

        if modifier == Date.MOD_TEXTONLY:
            return (Date.QUAL_NONE, Date.MOD_TEXTONLY, Date.CAL_GREGORIAN,
                    Date.EMPTY, text, Date.NEWYEAR_JAN1)

        quality = QUAL_TEXT[self.quality_box.get_active()][0]

        if modifier in (Date.MOD_RANGE, Date.MOD_SPAN):
            value = (
                self.start_day.get_value_as_int(),
                self.start_month_box.get_active(),
                self.start_year.get_value_as_int(),
                self.dual_dated.get_active(),
                self.stop_day.get_value_as_int(),
                self.stop_month_box.get_active(),
                self.stop_year.get_value_as_int(),
                self.dual_dated.get_active())
        else:
            value = (
                self.start_day.get_value_as_int(),
                self.start_month_box.get_active(),
                self.start_year.get_value_as_int(),
                self.dual_dated.get_active())
        calendar = self.calendar_box.get_active()
        newyear = Date.newyear_to_code(self.new_year.get_text())
        return (quality, modifier, calendar, value, text, newyear)

    def switch_type(self, obj):
        """
        Disable/enable various date controls depending on the date 
        type selected via the menu.
        """

        the_modifier = MOD_TEXT[self.type_box.get_active()][0]
        
        # Disable/enable second date controls based on whether
        # the type allows compound dates
        if the_modifier in (Date.MOD_RANGE, Date.MOD_SPAN):
            stop_date_sensitivity = 1
        else:
            stop_date_sensitivity = 0
        self.stop_day.set_sensitive(stop_date_sensitivity)
        self.stop_month_box.set_sensitive(stop_date_sensitivity)
        self.stop_year.set_sensitive(stop_date_sensitivity)

        # Disable/enable the rest of the controls if the type is text-only.
        date_sensitivity = not the_modifier == Date.MOD_TEXTONLY
        self.start_day.set_sensitive(date_sensitivity)
        self.start_month_box.set_sensitive(date_sensitivity)
        self.start_year.set_sensitive(date_sensitivity)
        self.calendar_box.set_sensitive(date_sensitivity)
        self.quality_box.set_sensitive(date_sensitivity)
        self.dual_dated.set_sensitive(date_sensitivity)
        self.new_year.set_sensitive(date_sensitivity)

    def switch_dual_dated(self, obj):
        """
        Changed whether this is a dual dated year, or not.
        Dual dated years are represented in the Julian calendar
        so that the day/months don't changed in the Text representation.
        """
        if self.dual_dated.get_active():
            self.calendar_box.set_active(Date.CAL_JULIAN)
            self.calendar_box.set_sensitive(0)
        else:
            self.calendar_box.set_sensitive(1)

    def switch_calendar(self, obj):
        """
        Change month names and convert the date based on the calendar 
        selected via the menu.
        """
        
        old_cal = self.date.get_calendar()
        new_cal = self.calendar_box.get_active()

        (the_quality, the_modifier, the_calendar, 
         the_value, the_text, the_newyear) = self.build_date_from_ui()
        self.date.set(
                quality=the_quality,
                modifier=the_modifier,
                calendar=old_cal,
                value=the_value,
                text=the_text,
                newyear=the_newyear)

        if not self.date.is_empty():
            self.date.convert_calendar(new_cal)
        
        self.start_month_box.get_model().clear()
        self.stop_month_box.get_model().clear()
        month_names = CAL_TO_MONTHS_NAMES[new_cal]
        for name in month_names:
            self.start_month_box.append_text(name)
            self.stop_month_box.append_text(name)

        self.start_day.set_value(self.date.get_day())
        self.start_month_box.set_active(self.date.get_month())
        self.start_year.set_value(self.date.get_year())
        self.stop_day.set_value(self.date.get_stop_day())
        self.stop_month_box.set_active(self.date.get_stop_month())
        self.stop_year.set_value(self.date.get_stop_year())
