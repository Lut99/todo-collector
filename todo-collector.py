#!/usr/bin/env python3
# TODO COLLECTOR.py
#   by Lut99
#
# Created:
#   16 Oct 2024, 17:32:14
# Last edited:
#   16 Oct 2024, 18:14:45
# Auto updated?
#   Yes
#
# Description:
#   Script for collecting my TODOs across my notes.
#

import argparse
import os
import sys
from io import TextIOWrapper
from typing import Generator, List, Optional


##### GLOBALS #####
# Whether to print additional debug statements or not.
DEBUG: bool = False





##### HELPER FUNCTIONS #####
def _supports_color():
    """
        Returns True if the running system's terminal supports color, and False
        otherwise.

        From: https://stackoverflow.com/a/22254892
    """
    plat = sys.platform
    supported_platform = plat != 'Pocket PC' and (plat != 'win32' or
                                                  'ANSICON' in os.environ)
    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    return supported_platform and is_a_tty

def pdebug(text: str, end: str = '\n', use_colour: Optional[bool] = None, file: TextIOWrapper = sys.stdout):
    """
        Prints a message as if it's debug statements.

        From: https://github.com/Lut99/logging-py/blob/main/logging.py#64-84

        # Arguments
        - `text`: The message to display.
        - `end`: Something to print at the end of the message. By default, this is a newline.
        - `use_colour`: Whether to use colour or not. Use `None` to try and deduce it automagically.
        - `file`: The file on which to write the message.
    """

    # Do nothing if not debugging
    if not DEBUG: return

    # Resolve colours
    use_colour = use_colour if use_colour is not None else _supports_color()
    accent = "\033[90;1m" if use_colour else ""
    clear = "\033[0m" if use_colour else ""

    # Print the message
    print(f"{accent}DEBUG: {text}{clear}", file=file, end=end)

def perror(text: str, end: str = '\n', use_colour: Optional[bool] = None, file: TextIOWrapper = sys.stderr):
    """
        Prints a message as if it's a fatal error.

        From: https://github.com/Lut99/logging-py/blob/main/logging.py#126-144

        # Arguments
        - `text`: The message to display.
        - `end`: Something to print at the end of the message. By default, this is a newline.
        - `use_colour`: Whether to use colour or not. Use `None` to try and deduce it automagically.
        - `file`: The file on which to write the message.
    """

    # Resolve colours
    use_colour = use_colour if use_colour is not None else _supports_color()
    accent = "\033[91;1m" if use_colour else ""
    bold = "\033[1m" if use_colour else ""
    clear = "\033[0m" if use_colour else ""

    # Print the message
    print(f"{accent}ERROR{clear}{bold}: {text}{clear}", file=file, end=end)





##### HELPERS #####
class Todo:
    # Whether its been done
    done: bool
    # Who does it
    who: str
    # What to do
    what: str
    # Where its gotten from
    file: str

    def __init__(self, done: bool, who: str, what: str, file: str):
        self.done = done
        self.who = who
        self.what = what
        self.file = file





##### AUXILLARY FUNCTIONS #####
def get_markdown_files(path: str, exclude: List[str]) -> Generator[str, None, None]:
    """
        Generator for finding all markdown files in a tree path.

        # Arguments
        - `path`: The file/folder to search.
        - `exclude`: The list of files to exclude from the search.

        # Returns
        Each of the files ending in `.md`.
    """

    # Canonicalize all excluded directories
    aexclude = []
    for e in exclude:
        try:
            aexclude.append(os.path.abspath(e))
        except IOError as e:
            perror(f"Failed to canonicalize to-be-excluded entry '{e}'")
            return None

    todo = [path]
    while len(todo) > 0:
        p = todo.pop()

        # Check if we should skip it
        try:
            if os.path.abspath(p) in aexclude:
                pdebug(f"get_markdown_files(): Excluding '{p}'")
                continue
        except IOError as e:
            perror(f"Failed to canonicalize entry '{p}'")
            return None

        # Decide what to do based on the type of the entry
        if os.path.isfile(p):
            pdebug(f"get_markdown_files(): Considering '{p}' as candidate Markdown file")

            # It's a file; store if ending in `.md`
            if len(p) >= 3 and p[-3:] == ".md":
                yield p
        elif os.path.isdir(p):
            pdebug(f"get_markdown_files(): Recursing into '{p}'")

            # It's a directory; add the children
            try:
                todo += [os.path.join(p, entry) for entry in os.listdir(p)]
            except IOError as e:
                perror(f"Failed to find entries of directory '{p}': {e}")
                return None
        else:
            perror(f"Path '{p}' is neither a file, nor a directory")
            return None

def analyze_todos_in_file(path: str, who: str) -> List[Todo]:
    """
        Finds the TODOs in the given file for the given person.

        # Arguments
        - `path`: The given file.
        - `who`: The given person.

        # Returns
        A list of all found `Todo`s.
    """

    # Read the file line-by-line
    todos = []
    with open(path, "r") as h:
        for line in h.readlines():
            # Check if the line Has What We Need TM
            if len(line) >= 3 and line[:3] == "- [":
                line = line[3:]

                # Check if it's a checkbox
                done = False
                if len(line) >= 4 and line[:4] == "x] [":
                    done = True
                    line = line[4:]
                elif len(line) >= 4 and line[:4] == " ] [":
                    line = line[4:]

                # Else, fetch the name
                if (pos := line.find(']')) >= 0:
                    name = line[:pos]
                    line = line[pos + 1:]
                else:
                    continue

                # The rest is what
                if name == who:
                    todos.append(Todo(done, name, line.strip(), path))
    return todos





##### ENTRYPOINT #####
def main(path: str, output: str, exclude: List[str], who: str, skip_done: bool) -> int:
    """
        Entrypoint to the script.

        # Arguments
        - `path`: The path to the file structure to analyse for TODOs.
        - `output`: The path to the file where we collect the TODOs.
        - `exclude`: The list of files to exclude from the search.
        - `who`: The name of the person to find TODOs for.
        - `skip_done`: Whether to print any TODOs that are done (False) or not (True).

        # Returns
        The intended exit code of the script. `0` means success.
    """

    # Debug print the input
    pdebug("todo-collector.py - v0.1.0")
    pdebug(f" - path    : \"{path}\"")
    pdebug(f" - output  : \"{output}\"")
    pdebug(f" - exclude : {exclude}")
    pdebug(f" - who     : \"{who}\"")

    # Start analyzing the files
    todos = []
    for file in get_markdown_files(path, exclude):
        try:
            todos += analyze_todos_in_file(file, who)
        except IOError as e:
            perror(f"Failed to analyze file '{file}': {e}")
            return e.errno

    # Write the result
    if output == "-":
        h = sys.stdout
    else:
        try:
            h = open(output, "w")
        except IOError as e:
            perror(f"Failed to open '{output}' for writing: {e}")
            return e.errno
    for todo in todos:
        if skip_done and todo.done: continue
        try:
            h.write(f"- [{'x' if todo.done else ' '}] [{todo.who}] {todo.what} ({todo.file})\n")
        except IOError as e:
            perror(f"Failed to write to '{output if output != '-' else 'stdout'}': {e}")
            return e.errno
    h.close()

    # Done!
    return 0


# Actual entrypoint
if __name__ == "__main__":
    # Define the arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("PATH", type=str, help="The path to the folder structure to scan for TODOs.")
    parser.add_argument("-o", "--output", type=str, default="-", help="The path to the file to write the TODOs to. Use '-' to write to stdout.")
    parser.add_argument("-e", "--exclude", nargs='*', type=str, help="Any files or directories that should be excluded from the scan.")
    parser.add_argument("-w", "--who", required=True, type=str, help="The name of the person to find TODOs for.")
    parser.add_argument("-s", "--skip-done", action="store_true", help="If given, only prints TODOs that are not yet done.")
    parser.add_argument("--debug", action="store_true", help="If given, shows additional DEBUG prints.")

    # Parse the arguments
    args = parser.parse_args()
    DEBUG = args.debug

    # Call main
    exit(main(args.PATH, args.output, args.exclude if args.exclude is not None else [], args.who, args.skip_done))
