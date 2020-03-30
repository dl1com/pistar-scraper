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

import argparse

import requests
from bs4 import BeautifulSoup

from lastheardentry import LastHeardEntry

from influxdb import InfluxDBClient


class PistarScraper(object):

    def setup_parser(self):
        self.parser = argparse.ArgumentParser(description='Scraping data from \
          a Pi-Star dashboard and write it into InfluxDB')
        self.parser.add_argument('--url', required=True,
                                 help='of the Pi-Star dashboard')
        self.parser.add_argument('--db_host', required=True,
                                 help='Hostname of the InfluxDB Server, \
                                 example: http://pi-star.local')
        self.parser.add_argument('--db_port',
                                 help='Port of the InfluxDB Server \
                                (default: ' + str(self.db_port) + ')')
        self.parser.add_argument('--db_name',
                                 help='Name of the InfluxDB database \
                                 (default: ' + self.db_name + ')')

    def parse_arguments(self):
        """Read commandline arguments and store content to local variables"""
        args = self.parser.parse_args()

        self.url = args.url
        self.db_host = args.db_host

        if args.db_port is not None:
            self.db_port = args.db_port
        if args.db_name is not None:
            self.db_name = args.db_name

    def read_lastheard_entries_from_pistar(self):
        """Download Pi-Star's "last heard" table and extract information into
          a list of LastHeardEntrys"""
        print("Getting Pi-Star Page...")

        # Scrape "last heard" page from Pi-Star
        entries = []
        url = self.url + "/mmdvmhost/lh.php"
        try:
            soup = BeautifulSoup(requests.get(url, verify=False).text,
                                 'html5lib')
        except:
            print("Could not connect to '" + url + "'")
            exit()

        table = soup.body.table.tbody
        rows = table.find_all('tr')

        # Step through the list and convert rows to LastHeardEntry objects
        print("Parsing " + str(len(rows)-1) + " entries...")
        for row in rows:
            cols = row.find_all("td")

            try:
                entry = LastHeardEntry(cols)
            except:
                continue

            entry.print()
            entries.append(entry)
        return entries

    def connect_to_InfluxDB(self):
        """Establish connection to InfluxDB and return client object"""
        try:
            client = InfluxDBClient(host=self.db_host, port=self.db_port)
        except:
            print("Could not connect to InfluxDB on " + self.db_host
                  + ":" + str(self.db_port))
            exit()
        client.create_database(self.db_name)
        client.switch_database(self.db_name)
        return client

    def write_entries_to_InfluxDB(self, client, entries):
        """Write the list of entries into the database"""
        print("Writing entries to InfluxDB")
        for entry in entries:
            client.write_points(entry.get_JSON_for_Influx())

    def run(self):
        self.setup_parser()
        self.parse_arguments()

        entries = self.read_lastheard_entries_from_pistar()
        client = self.connect_to_InfluxDB()
        self.write_entries_to_InfluxDB(client, entries)
        client.close()
        exit()

    def __init__(self):
        """Default settings"""
        self.url = ""
        self.db_host = ""
        self.db_port = 8086
        self.db_name = "pistar"


if __name__ == '__main__':
    scraper = PistarScraper()
    scraper.run()
