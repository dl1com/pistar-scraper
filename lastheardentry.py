#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# This file is part of pistar-scraper
#
# MIT License
#
# Copyright (c) 2020 Christian Obersteiner DL1COM
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import datetime
import pytz


class LastHeardEntry(object):
    """Class for storing a "last heard" entry"""

    def parse_columns(self, cols):
        """Read columns of a line and insert data into member-variables"""
        if (len(cols) != 8):
            raise ValueError

        self.timestamp = self.string_to_timestamp(cols[0].get_text())
        self.mode = cols[1].get_text()
        self.callsign = cols[2].get_text()

        # Remove non-blankspace from string
        self.target = cols[3].get_text().replace(u'\xa0', u' ')
        self.source = cols[4].get_text()

        # If transmission is still ongoing, ignore this line
        duration = cols[5].get_text()
        if (duration != "TX"):
            self.duration = float(duration)
        else:
            raise ValueError

        self.loss = int(cols[6].get_text()[:-1])

        # If no BER is given, ignore (we have to keep the data numeric-only)
        ber = cols[7].get_text()[:-1]
        if (ber != "??"):
            self.ber = float(ber)

        return

    def string_to_timestamp(self, s):
        """Source format: '15:10:34 Mar 25th'"""
        currentYear = (datetime.date.today().strftime("%Y"))
        # We have to add the current year to have a complete datetime
        # TODO handle wrap on new year
        # TODO Expose Timezone setting as commandline parameter
        s = s[:-2] + " " + currentYear
        timestamp = datetime.datetime.strptime(s, "%H:%M:%S %b %d %Y")
        timestamp = pytz.timezone('Europe/Berlin').localize(timestamp)
        timestamp = timestamp.astimezone(pytz.utc)
        return timestamp

    def print(self):
        """Pretty-printing object contents"""
        print(self.timestamp.isoformat() + "\t" + self.mode + "\t"
              + self.callsign + "\t" + self.target + "\t" + self.source + "\t"
              + str(self.duration) + "\t" + str(self.loss) + "%\t"
              + str(self.ber) + "%")

    def get_JSON_for_Influx(self):
        """ Format JSON object for insertion to InfluxDB"""
        json_body = [
            {
                "measurement": "last_heard",
                "time": self.timestamp.isoformat(),
                "fields": {
                  "mode": self.mode,
                  "callsign": self.callsign,
                  "target": self.target,
                  "source": self.source,
                  "duration": self.duration,
                  "loss": self.loss,
                  "ber": self.ber
                }
            }
        ]
        return json_body

    def init(self):
        """Set member-variables to default values"""
        self.timestamp = datetime.datetime(1970, 1, 1)
        self.mode = "unkown"
        self.callsign = "unkown"
        self.target = "unknown"
        self.source = "unkown"
        self.duration = 0.0
        self.loss = 0
        self.ber = 0.0

    def __init__(self, cols=None):
        self.init()

        if (cols is not None):
            self.parse_columns(cols)
