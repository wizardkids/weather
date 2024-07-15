"""
    Filename: r_utils.py
     Version: 0.1
      Author: Richard E. Rawson
        Date: 2024-03-26
 Description: A collection of utilities that are frequently useful.

Functions:
    flatten_list
    fold
    get_time
    print_documentation
    sort_item
"""

import ast
import json
import textwrap
import time
from collections import OrderedDict
from pathlib import Path

# from icecream import ic


def get_time(func):
    """
    get_time() is custom operator designed to make timing a function really easy. Once we create get_time(), all we need to do is put the @get_time decorator over any function to time it.
    """
    # @wraps(func)
    def wrapper(*args, **kwargs):
        start_time: float = time.perf_counter()

        func(*args, *kwargs)
        end_time: float = time.perf_counter()
        total_time: float = round(end_time - start_time, 2)
        print(f'Time: {total_time} seconds')

    return wrapper


def fold(txt_str: str, width: int = 50, indent: int = 0) -> str:
    """
    Wraps multi-line strings, such as docstrings, at a specified width with specified indent.

    Parameters
    ----------
    txt_str : str -- any string
    width : int, optional -- width of the printed text, by default 50
    indent : int, optional -- indent amount, by default 0

    Returns
    -------
    str -- formatted string

    Example
    -------
    txt = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation"

    folded_txt = f'{fold(txt, 70, 4)}'
    print(folded_txt)

    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
    eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad
    minim veniam, quis nostrud exercitation
    """

    if txt_str is None:
        return ""

    # Split "txt_str" into lines
    lines: list[str] = txt_str.strip().split('\n')

    # Initialize an empty list to hold the formatted lines
    formatted_lines: list[str] = []

    # Process each line
    for line in lines:
        wrapped_txt: str = textwrap.fill(line, width)
        indented_txt: str = textwrap.indent(wrapped_txt, " " * indent)
        formatted_lines.append(indented_txt)

    # Join the formatted lines into a single string
    formatted_txt: str = '\n'.join(formatted_lines)

    return formatted_txt


def print_documentation(file: str = None, function_names_only=False) -> None:
    """
    Prints the names and docstrings of functions in the given .py file. Absolute path to "file" is required even if this module is imported.

    Function names and docstrings are first added to a dictionary ({name:docstring}), which is then saved as "function_docstrings.json" before printing content to the terminal.

    When importing r_utils into a .py file, use:

        r_utils.print_documentation(__file__)

    to access the functions/docstrings of the current .py file.

    Parameters
    ----------
    file : str, optional -- path for file
    function_names_only : bool, optional -- print only the function names, by default False

    Example
    -------
    print_documentation("c:\\foo\\bar.py") --> prints all function names with docstrings
    print_documentation(__file__) --> print data for the current .py file
    """

    if file is None:
        print("\nError: File path is required.\nTry including absolute path.")
        exit()

    file_path = Path(file)
    # Get the path part of "fp_path".
    directory: str = str(file_path.parent)
    if file_path.exists():
        file_str = str(file_path)
    else:
        print("\nError: File does not exist.\nTry including absolute path.")
        exit()

    doc_dict: dict[str, str] = {}
    with open(file_str, "r") as file:

        try:
            node = ast.parse(file.read())
        except UnicodeDecodeError:
            print(f'Cannot decode docstring. Try using a different encoding.')
            exit()

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                docstring: str | None = ast.get_docstring(item)
                doc_dict = {item.name: ast.get_docstring(
                    item) for item in node.body if isinstance(item, ast.FunctionDef)}

    docstring_file = directory + "\\function_docstrings.json"
    with open(docstring_file, 'w') as json_file:
        json.dump(doc_dict, json_file, indent=4)

    for k, v in doc_dict.items():
        print(f'{k}', sep="", end="")
        if not function_names_only:
            print('\n', fold(v, 70, 4), "\n", sep="")
        else:
            print()


def sort_item(original_item: list | dict, reversed=False, sort_element: int = 0) -> list | OrderedDict | None:
    """
    This function is a Swiss-Army knife for sorting a list, a list of lists|tuples, or a dictionary. The sorted item can optionally be reversed.

    If a list of lists|tuples is passed in, the lists or tuples will be sorted on the first item in each item, by default. If the "sort_element" argument is invalid, the lists or tuples will be sorted on the first element. "sort_element" is ignored for one-dimensional lists.

    If a dictinary is passed in, an OrderedDict is returned, since the OrderedDict type retains a sort order. "sort_element" can be used to sort on the key (0) or the value (1).

    sort_list() will raise an IndexError if any list|tuple in a list does not have at least as many elements as "sort_element".

    Parameters
    ----------
    original_item : list -- list, list of tuples, or dictionary
    reversed : bool, optional -- if True, reverse the order, by default False
    sort_element : int -- the element on which to sort

    Returns
    -------
    list -- sorted item: a list or an OrderedDict

    Example:
    -------
    list_of_lists = [["z", "a"], ["j", "c"], ["b", "e"]]
    sort_list(list_of_lists, reversed=False, sort_element=1)

    [['z', 'a'], ['j', 'c'], ['b', 'e']]
    """
    # If the item is a list of list|tuple, and sort_element is ok...
    if (isinstance(original_item, list)) and \
        (isinstance(original_item[0], (tuple, list))) and \
            (0 <= sort_element < len(original_item[0])):

        try:
            sorted_item = sorted(
                original_item, key=lambda x: x[sort_element], reverse=reversed)
        except IndexError:
            print("\nOne or more elements in the provided list\ndoes not have enough elements to sort, given\nthe value of \"sort_elements\".")
            return None

    # If the item is a dictionary, sort on key or value...
    elif (isinstance(original_item, dict)) and (sort_element in [0, 1]):
        # sorted_item = OrderedDict(sorted(original_item.items(), reverse=reversed))
        sorted_item = OrderedDict(
            sorted(original_item.items(), key=lambda item: item[sort_element]))

    # If the item is a one_dimensional list...
    elif isinstance(original_item, list):
        sorted_item = sorted(original_item, reverse=reversed)

    else:
        print("Cannot sort item passed in.")
        return None

    return sorted_item


def flatten_list(target) -> list | str:
    """
    Flattens an n-dimensional list into a one-dimensional list. "n" can be any value. The list does not need to be consistent, meaning this function can handle a complex list such as:

        lst = ["a", "b", ["z", [["a", "j", ["c", "b"]]]], ["z", ["a", "k"]], ["j", "c", "k"], ["b", "a", "z"]]

    Parameters
    ----------
    target : list -- any n-dimensional list

    Returns
    -------
    list -- flattened list
    """
    if isinstance(target, list):
        return sum((flatten_list(sub) if isinstance(sub, list) else [sub] for sub in target), [])
    else:
        return f'{target} is not a list'


if __name__ == '__main__':

    lst = ["z", "a", "j", "c", "b"]
    lstlst = [["z", "a", "k"], ["j", "c", "k"], ["b", "a", "z"]]
    tuple_lst = [("z", 26), ("a", 1), ("j", 10), ("c", 3), ("b", 2), ("d", 0)]
    original_dict = {"z": 26, "a": 1, "j": 10, "c": 3, "b": 2}

    sorted_item = sort_item(lstlst, reversed=False, sort_element=1)

    print_documentation(__file__, True)
