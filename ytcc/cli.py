# ytcc - The YouTube channel checker
# Copyright (C) 2015  Wolfgang Popp
#
# This file is part of ytcc.
#
# ytcc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ytcc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ytcc.  If not, see <http://www.gnu.org/licenses/>.

from ytcc import core
from dateutil import parser as date_parser
from datetime import datetime
import shutil
import argparse
import os
import textwrap as wrap

ytcc_core = core.Ytcc()
interactive_enabled = True
description_enabled = True
table_header = ["ID", "Date", "Channel", "Title", "URL"]
column_filter = None
header_enabled = True


def update_all():
    print("Updating channels...")
    ytcc_core.update_all()


def print_description(description):
    global description_enabled
    if description_enabled:
        columns = shutil.get_terminal_size().columns
        delimiter = "=" * columns
        lines = description.splitlines()

        print("\nVideo description:")
        print(delimiter)

        for line in lines:
            print(wrap.fill(line, width=columns))

        print(delimiter, end="\n\n")


def play_videos(videos, interactive):
    for video in videos:
        if interactive:
            choice = input('Play video "' + video.title + '" by "' + video.channelname +
                           '"?\n[y(es)/n(o)/m(ark)/q(uit)] (Default: y): ')
        else:
            print('Playing "' + video.title + '" by "' + video.channelname + '"...')
            choice = "y"

        if choice in ("y", "Y", "", "yes"):
            print_description(video.description)
            if not ytcc_core.play_video(video.id):
                print("\nWARNING: The video player terminated with an error.")
                print("         The last video is not marked as watched!\n")
        elif choice in ("m", "M", "mark"):
            ytcc_core.mark_some_watched([video.id])
        elif choice in ("q", "Q", "quit"):
            break


def watch(video_ids=None):
    if not video_ids:
        _videos = ytcc_core.list_videos()
        if not _videos:
            print("No videos to watch. No videos match the given criteria.")
        else:
            play_videos(_videos, interactive_enabled)
    else:
        play_videos(ytcc_core.get_videos(video_ids), False)


def table_print(header, table):
    col_widths = []
    header_line = ""

    for h in header:
        col_widths.append(len(h))

    for i in range(0, len(header)):
        col_widths[i] = max(map(lambda h: len(str(h[i])), table))

    for width in col_widths:
        header_line += "─" * (width + 2)
        header_line += "┼"

    header_line = header_line[:-1]
    format = (" {{:<{}}} │" * len(header))[:-2].format(*col_widths)

    if header_enabled:
        print(format.format(*header))
        print(header_line)

    for row in table:
        print(format.format(*row))


def print_videos():
    videos = ytcc_core.list_videos()
    if not videos:
        print("No videos to list. No videos match the given criteria.")
    else:
        table_format = ytcc_core.config["TableFormat"]

        if column_filter:
            table_col_filter = column_filter
        else:
            table_col_filter = [table_format.getboolean("ID"),
                                table_format.getboolean("Date"),
                                table_format.getboolean("Channel"),
                                table_format.getboolean("Title"),
                                table_format.getboolean("URL")]

        def row_filter(row):
            return list(map(lambda e: e[1], filter(lambda e: e[0], zip(table_col_filter, row))))

        def video_to_list(video):
            return [video.id, datetime.fromtimestamp(video.publish_date).strftime("%Y-%m-%d %H:%M"),
                    video.channelname, video.title, ytcc_core.get_youtube_video_url(video.yt_videoid)]

        table = [row_filter(video_to_list(v)) for v in videos]
        table_print(row_filter(table_header), table)


def print_channels():
    channels = ytcc_core.list_channels()
    if not channels:
        print("No channels added, yet.")
    else:
        for channel in channels:
            print(channel.displayname)


def download(video_ids, path):
    ids = video_ids if video_ids else map(lambda video: video.id, ytcc_core.list_videos())
    ytcc_core.download_videos(ids, path)


def add_channel(name, channel_url):
    try:
        ytcc_core.add_channel(name, channel_url)
    except core.BadURLException as e:
        print(e.message)
    except core.DuplicateChannelException as e:
        print(e.message)
    except core.ChannelDoesNotExistException as e:
        print(e.message)


def mark_watched(video_ids):
    if not video_ids or video_ids[0] == "all":
        ytcc_core.mark_watched()
    else:
        ytcc_core.mark_some_watched(video_ids)


def cleanup():
    print("Cleaning up database...")
    ytcc_core.cleanup()


def import_channels(file):
    print("Importing...")
    try:
        ytcc_core.import_channels(file)
        print("\nSubscriptions")
        print("=============")
        print_channels()
    except core.InvalidSubscriptionFile as e:
        print(e.message)


def is_directory(string):
    if not os.path.isdir(string):
        msg = "%r is not a directory" % string
        raise argparse.ArgumentTypeError(msg)

    return string


def is_date(string):
    try:
        date_parser.parse(string)
    except ValueError:
        msg = "%r is not a valid date" % string
        raise argparse.ArgumentTypeError(msg)

    return string


def main():

    parser = argparse.ArgumentParser(description="ytcc is a commandline YouTube client that keeps track of your "
                                     "favorite channels. The --list, --watch, --download, --mark-watched options can "
                                     "be combined with filter options --channel-filter, --include-watched, --since, "
                                     "--to")

    parser.add_argument("-a", "--add-channel",
                        help="add a new channel. NAME is the name displayed by ytcc. URL is"
                        " the url of the channel's front page",
                        nargs=2,
                        metavar=("NAME", "URL"))

    parser.add_argument("-c", "--list-channels",
                        help="print a list of all subscribed channels",
                        action="store_true")

    parser.add_argument("-r", "--delete-channel",
                        help="unsubscribe from the channel identified by 'ID'",
                        metavar="ID",
                        nargs='+',
                        type=str)

    parser.add_argument("-u", "--update",
                        help="update the video list",
                        action="store_true")

    parser.add_argument("-l", "--list",
                        help="print a list of videos that match the criteria given by the filter options",
                        action="store_true")

    parser.add_argument("-w", "--watch",
                        help="play the videos identified by 'ID'. Omitting the ID will "
                        "play all videos specified by the filter options",
                        nargs='*',
                        type=int,
                        metavar="ID")

    parser.add_argument("-d", "--download",
                        help="download the videos identified by 'ID'. The videos are saved "
                        "in $HOME/Downloads by default. Omitting the ID will download "
                        "all videos that match the criteria given by the filter options",
                        nargs="*",
                        type=int,
                        metavar="ID")

    parser.add_argument("-m", "--mark-watched",
                        help="mark videos identified by ID as watched. Omitting the ID "
                        "will mark all videos that match the criteria given by the filter options as watched",
                        nargs='*',
                        type=int,
                        metavar="ID")

    parser.add_argument("-f", "--channel-filter",
                        help="plays, lists, marks, downloads only videos from channels defined in "
                        "the filter",
                        nargs='+',
                        type=str,
                        metavar="NAME")

    parser.add_argument("-n", "--include-watched",
                        help="include already watched videos to filter rules",
                        action="store_true")

    parser.add_argument("-s", "--since",
                        help="includes only videos published after the given date",
                        metavar="YYYY-MM-DD",
                        type=is_date)

    parser.add_argument("-t", "--to",
                        help="includes only videos published before the given date",
                        metavar="YYYY-MM-DD",
                        type=is_date)

    parser.add_argument("-p", "--path",
                        help="set the download path to PATH",
                        metavar="PATH",
                        type=is_directory)

    parser.add_argument("-g", "--no-description",
                        help="do not print the video description before playing the video",
                        action="store_true")

    parser.add_argument("-o", "--columns",
                        help="specifies which columns will be printed when listing videos. COL can be any of "
                        + str(table_header),
                        nargs='+',
                        metavar="COL",
                        choices=table_header)

    parser.add_argument("--no-header",
                        help="do not print the header of the table when listing videos",
                        action="store_true")

    parser.add_argument("-y", "--yes",
                        help="automatically answer all questions with yes",
                        action="store_true")

    parser.add_argument("--import-from",
                        help="import YouTube channels from YouTube's subscription export (available at "
                        "https://www.youtube.com/subscription_manager)",
                        metavar="PATH",
                        type=argparse.FileType("r"))

    parser.add_argument("--cleanup",
                        help="removes old videos from the database and shrinks the size of the database file",
                        action="store_true")

    parser.add_argument("-v", "--version",
                        help="output version information and exit",
                        action="store_true")

    args = parser.parse_args()

    option_executed = False

    if args.version:
        import ytcc
        print("ytcc version " + ytcc.__version__)
        print()
        print("Copyright (C) 2015-2016  " + ytcc.__author__)
        print("This program comes with ABSOLUTELY NO WARRANTY; This is free software, and you")
        print("are welcome to redistribute it under certain conditions.  See the GNU General ")
        print("Public Licence for details.")
        return

    if args.yes:
        global interactive_enabled
        interactive_enabled = False

    if args.no_description:
        global description_enabled
        description_enabled = False

    if args.no_header:
        global header_enabled
        header_enabled = False

    if args.columns:
        global column_filter
        column_filter = [True if f in args.columns else False for f in table_header]

    if args.channel_filter:
        ytcc_core.set_channel_filter(args.channel_filter)

    if args.since:
        ytcc_core.set_date_begin_filter(date_parser.parse(args.since))

    if args.to:
        ytcc_core.set_date_end_filter(date_parser.parse(args.to))

    if args.include_watched:
        ytcc_core.set_include_watched_filter()

    if args.import_from:
        import_channels(args.import_from)
        option_executed = True

    if args.cleanup:
        cleanup()
        option_executed = True

    if args.add_channel:
        add_channel(*args.add_channel)
        option_executed = True

    if args.list_channels:
        print_channels()
        option_executed = True

    if args.delete_channel:
        ytcc_core.delete_channels(args.delete_channel)
        option_executed = True

    if args.update:
        if option_executed:
            print()
        update_all()
        option_executed = True

    if args.list:
        if option_executed:
            print()
        print_videos()
        option_executed = True

    if args.download is not None:
        download(args.download, args.path)
        option_executed = True

    if args.watch is not None:
        if option_executed:
            print()
        watch(args.watch)
        option_executed = True

    if args.mark_watched is not None:
        mark_watched(args.mark_watched)
        option_executed = True

    if not option_executed:
        update_all()
        print()
        watch()
