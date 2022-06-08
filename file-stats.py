#!/usr/bin/python3
#
# Basic tool to split multiple statistics written by BIND9 into separate lines

import sys
import re
import json

STATS_ENTRY = re.compile(r'\+\+\+ ([^\+]*) \+\+\+ \((\d+)\)')
STATS_FINAL = re.compile(r'--- ([^-]*) --- \((\d+)\)')
STATS_SECTION = re.compile(r'\+\+ ([^+]*) \+\+')
STATS_SUBSECTION = re.compile(r'\[([^\]]*)\]')
STATS_VALUE = re.compile(r'\s*(\d+) (.*)\s*')
DEBUG = False

class Section(object):
    """ One section or subsection """

    def __init__(self, name):
        self.name = name
        self.sections = {}
        self.values = {}

    def add_section(self, section):
        self.sections[section.name] = section
        if DEBUG:
            print("Adding section {}".format(section.name))

    def add_value(self, key, value):
        v = int(value)
        self.values[key] = v
        if DEBUG:
            print("Adding value {}={}".format(key, v))
        return v

    def json(self):
        d = {'name': self.name}
        if self.sections:
            d.update(self.sections)
            #d['sections'] = self.sections
        if self.values:
            d['values'] = self.values
        return d

class Bundle(object):
    """ One complete dump of statistics """

    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.sections = {}

    def add_section(self, section):
        if DEBUG:
            print("Adding section {}".format(section.name))
        self.sections[section.name] = section

    def json(self):
        d = {'timestamp': self.timestamp}
        d.update(self.sections)
        return d

def add_bundle(bundle):
    print(json.dumps(bundle, default=encode_json, indent=2))

def parse_input(file):
    bundle = None
    section = None
    subsection = None
    all_bundles = []
    for line in file:
        m = STATS_ENTRY.match(line)
        if m:
            assert(m.group(1) == "Statistics Dump")
            bundle = Bundle(int(m.group(2)))
            continue
        m = STATS_FINAL.match(line)
        if m:
            timestamp = int(m.group(2))
            assert(timestamp == bundle.timestamp)
            if subsection:
                assert(section)
                section.add_section(subsection)
            if section:
                bundle.add_section(section)
            add_bundle(bundle)
            if DEBUG:
                print("Finished timestamp {}".format(timestamp))
            bundle = None
            section = None
            subsection = None
            continue
        m = STATS_SECTION.match(line)
        if m:
            assert(bundle)
            if subsection:
                section.add_section(subsection)
                subsection = None
            if section:
                bundle.add_section(section)
            section = Section(m.group(1))
            continue
        m = STATS_SUBSECTION.match(line)
        if m:
            assert(section)
            if subsection:
                section.add_section(subsection)
            subsection = Section(m.group(1))
            continue
        m = STATS_VALUE.match(line)
        if m:
            val = m.group(1)
            key = m.group(2)
            if subsection:
                subsection.add_value(key, val)
                continue
            elif section:
                section.add_value(key, val)
                continue
        print("Unmatched line: {}".format(line))

    if subsection and section:
        section.add_section(subsection)
    if section and bundle:
        bundle.add_section(section)
    if bundle:
        all_bundles.append(bundle)
    return all_bundles

def encode_json(obj):
    if isinstance(obj, Section):
        return obj.json()
    elif isinstance(obj, Bundle):
        return obj.json()

def print_bundles(bundles):
    for bundle in bundles:
        print(json.dumps(bundle, default=encode_json, indent=2))

if len(sys.argv)>1:
    for path in sys.argv[1:]:
        with open(path, 'r') as file:
            bundles = parse_input(file)
            print_bundles(bundles)
else:
    parse_input(sys.stdin)
