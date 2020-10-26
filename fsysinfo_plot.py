#!/usr/bin/python3 -B

"""
    fsysinfo_plot.py

    Copyright (C) 2020-2020 Klarälvdalens Datakonsult AB, a KDAB Group company, info@kdab.com

    Author: Sven Erdem <sven.erdem@kdab.com>

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""

import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
import random
import math
import sys

def print_help():
    for arg in sys.argv[1:]:
        if arg == "--help":
            print("this script plots a qnx fsysinfo log")
            print("usage")
            print("\tfsysinfo_plot.py [OPTION]... FILE -- KEY...")
            print()
            print("\twhereas the key determines what shall be printed")
            print("\tthe keys are formatted like so: \"SYSCALL.rename\"")
            print("example")
            print("\tfsysinfo_plot.py --diff my_fsysinfo_log -- SYSCALL.open \"DISK I/O.read\" \"DISK I/O.write\"")
            print("options")
            print("\t--stackplot  \tperforms a stackplot instead of a usual one")
            print("\t--diff       \tcalculates the difference between 2 samples")
            print("\t--avg N      \taverages between N samples (applied after diff)")
            print("\t--log        \tlogarithmic scale (be careful with negative values or when using diff)")
            print("\t--legendright\tdisplay legend on the top right instead of top left corner")
            print("keys")
            print("\tDISK I/O\tread, r/a, write, io req, direct, bad, read.bytes, r/a.bytes, write.bytes, io req.bytes, direct.bytes")
            print("\tCACHE   \tread, write, mfu, mru, ratio, read.bytes, write.bytes")
            print("\tSYSCALL \topen, create, delete, trunc, stat, namei, modes, owner, rename, devctl, sync, pause, change, timed, write, read, write.bytes, read.bytes")
            print("\tNAMES   \texist, enoent, misses, unsuit, stale, rate")
            print("\tBMAP    \thit, miss, rate")
            print("\tVNODES  \tcreate, hit, rate, lock, recycl")
            print("\tSLAB    \tmap, unmap, active")
            print("\tTHREADS \tcreate, destro, pool")
            print()
            print("recording a log is possible with `fsysinfo -l PERIOD`")
            print("whereas PERIOD is in milliseconds")
            return True
    return False

printable = ["read", "r/a", "write", "io req", "direct", "bad", "read", "write", "mfu", "mru", "ratio", "open", "create", "delete", "trunc", "stat", "namei", "modes", "owner", "rename", "devctl", "sync", "pause", "change", "timed", "write", "read", "exist", "enoent", "misses", "unsuit", "stale", "rate", "hit", "miss", "rate", "create", "hit", "rate", "lock", "recycl", "map", "unmap", "active", "create", "destro", "pool"]

def parse(filepath):
    f = open(filepath, "r")
    print(("opened " + filepath) if not f.closed else ("unable to open " + filepath) )
    lines = f.readlines()
    f.close()

    lines = lines[0 : len(lines) - (len(lines) % 24)] # cut away unfinished prints (24 lines for each print)
    lines = "  ".join(lines)
    lines = lines.split("  ")
    lines = map(lambda x: x.strip(), lines)
    lines = filter(lambda x: len(x) > 0, lines)
    lines = list(lines)

    base_key = ""
    key = ""
    should_append = False
    dic = dict()
    for line in lines:
        if line.isupper(): # begin a category
            should_append = False
            base_key = line
        else:
            is_key = any(line in s for s in printable)
            is_bytes = line == "bytes"
            if is_key or is_bytes:
                if is_key:
                    key = base_key + "." + line
                elif is_bytes:
                    should_append = True
                    key = key + ".bytes"

                should_append = True
                if not key in dic:
                    dic[key] = list()
            elif should_append:
                line = line[:-1] if line[-1] == "k" else line
                line = line[:-1] if line[-1] == "%" else line
                line = int(line)
                dic[key].append(line)

    return dic

def diff(dic):
    diff_dic = dict()
    for key in dic:
        diff_dic[key] = list()
        for i in range(len(dic[key]) - 1):
            diff_dic[key].append(dic[key][i + 1] - dic[key][i])
    return diff_dic

def average(dic, size):
    avg_dic = dict()
    for key in dic:
        avg_dic[key] = list()
        length = len(dic[key])
        for i in [x for x in range(length) if x % size == 0]:
            avg = [dic[key][i + j] for j in range(size) if i + j < length]
            avg = sum(avg) / len(avg)
            avg_dic[key].append(avg)
    return avg_dic

def min_plot_len(dic, keys):
    return min(map(lambda key: len(dic[key]), keys))

def do_stackplot(dic, keys, logscale=False, legendright=False):
    min_len = min_plot_len(dic, keys)

    fig, ax = plt.subplots()

    datas = list()
    for key in keys:
        data = dic[key][:min_len]
        datas.append(data)
        length = len(data)

    ax.stackplot(range(length), datas, labels = keys)

    ax.set(xlabel='sample', ylabel='value', title='fsysinfo_plot')
    ax.grid(True)
    ax.legend(loc='upper right' if legendright else 'upper left')
    if logscale:
        ax.set_yscale('log')
    plt.show()

def do_plot(dic, keys, logscale=False, legendright=False):
    min_len = min_plot_len(dic, keys)

    fig, ax = plt.subplots()

    for key in keys:
        data = dic[key][:min_len]
        ax.plot(range(len(data)), data, label = key)

    ax.set(xlabel='sample', ylabel='value', title='fsysinfo_plot')
    ax.grid(True)
    ax.legend(loc='upper right' if legendright else 'upper left')
    if logscale:
        ax.set_yscale('log')
    plt.show()

def parse_args():
    stackplot = False
    diffplot = False
    logscale = False
    filepath = ""
    legendright = False
    keys = list()
    parsing_keys = False
    avg = 1
    parsing_avg = False
    for arg in sys.argv[1:]:
        if parsing_keys:
            keys.append(arg)
        elif parsing_avg:
            avg = int(arg)
            parsing_avg = False
        else:
            if arg == "--stackplot":
                stackplot = True
            elif arg == "--diff":
                diffplot = True
            elif arg == "--log":
                logscale = True
            if arg == "--legendright":
                legendright = True
            elif arg == "--":
                parsing_keys = True
            elif arg == "--avg":
                parsing_avg = True
            else:
                filepath = arg
    return stackplot, diffplot, avg, logscale, legendright, filepath, keys

if not print_help():
    stackplot, diffplot, avg, logscale, legendright, filepath, keys = parse_args()
    dic = parse(filepath)
    if diffplot: dic = diff(dic)
    if avg > 1: dic = average(dic, avg)
    if stackplot:
        do_stackplot(dic, keys, logscale, legendright)
    else:
        do_plot(dic, keys, logscale, legendright)
