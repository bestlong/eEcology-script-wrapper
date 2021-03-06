# Copyright 2013 Netherlands eScience Center
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import iso8601
import colander


class Invalid(Exception):
    pass


def validateRange(count, minimum, maximum, tracker_id=None):
    """Validator which succeeds if the value it is passed is greater
    or equal to ``minimum`` and less than or equal to ``maximum``.

    Validator fails by raising a :exc:`Invalid` exception.
    """
    if tracker_id is None:
        if count > maximum:
            raise Invalid('Too many data points selected for this script, '
                          + 'selected {} data points while maximum is {}, '.format(count, maximum)
                          + 'please reduce time range and/or number of trackers')
        if count <= minimum:
            raise Invalid('No data points selected for this script, '
                          + 'please increase or shift time range')
    else:
        if count > maximum:
            raise Invalid('Too many data points selected for this script, '
                          + 'selected {} data points while maximum is {} for tracker {}, '.format(count, maximum, tracker_id)
                          + 'please reduce time range and/or number of trackers')
        if count <= minimum:
            raise Invalid('No data points selected for tracker {} for this script, '.format(tracker_id)
                          + 'please increase or shift time range')
    return True


def colorValidator(node, value):
    if (value[0] != '#'):
        msg = '%r is not a color, should be #RRGGBB' % value
        raise colander.Invalid(node, msg)

    try:
        int(value[1:], 16)
    except ValueError:
        msg = '%r is not a color, should be #RRGGBB' % value
        raise colander.Invalid(node, msg)


def iso8601Validator(node, value):
    try:
        iso8601.parse_date(value)
    except iso8601.ParseError:
        raise colander.Invalid(node, 'Invalid date')
