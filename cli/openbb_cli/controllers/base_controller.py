"""Base controller for the CLI."""

import argparse
import difflib
import os
import re
from abc import ABCMeta, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from openbb_cli.config import setup
from openbb_cli.config.completer import NestedCompleter
from openbb_cli.config.constants import SCRIPT_TAGS
from openbb_cli.controllers.choices import build_controller_choice_map
from openbb_cli.controllers.hub_service import upload_routine
from openbb_cli.controllers.utils import (
    check_file_type_saved,
    check_positive,
    get_flair_and_username,
    parse_and_split_input,
    print_guest_block_msg,
    remove_file,
    system_clear,
)
from openbb_cli.session import Session
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

# pylint: disable=C0301,C0302,R0902,global-statement,too-many-boolean-expressions
# pylint: disable=R0912

controllers: Dict[str, Any] = {}


# TODO: We should try to avoid these global variables
RECORD_SESSION = False
RECORD_SESSION_LOCAL_ONLY = False
SESSION_RECORDED = list()
SESSION_RECORDED_NAME = ""
SESSION_RECORDED_DESCRIPTION = ""
SESSION_RECORDED_TAGS = ""
SESSION_RECORDED_PUBLIC = False


class BaseController(metaclass=ABCMeta):
    """Base class for a cli controller."""

    CHOICES_COMMON = [
        "cls",
        "home",
        "about",
        "h",
        "?",
        "help",
        "q",
        "quit",
        "..",
        "e",
        "exit",
        "r",
        "reset",
        "stop",
        "hold",
        "whoami",
    ]

    CHOICES_COMMANDS: List[str] = []
    CHOICES_MENUS: List[str] = []
    HOLD_CHOICES: dict = {}
    NEWS_CHOICES: dict = {}
    COMMAND_SEPARATOR = "/"
    KEYS_MENU = "keys" + COMMAND_SEPARATOR
    PATH: str = ""
    FILE_PATH: str = ""
    CHOICES_GENERATION = False

    @property
    def choices_default(self):
        """Return the default choices."""
        choices = (
            build_controller_choice_map(controller=self)
            if self.CHOICES_GENERATION
            else {}
        )

        return choices

    def __init__(self, queue: Optional[List[str]] = None) -> None:
        """Create the base class for any controller in the codebase.

        Used to simplify the creation of menus.

        queue: List[str]
            The current queue of jobs to process separated by "/"
            E.g. /stocks/load gme/dps/sidtc/../exit
        """
        self.check_path()
        self.path = [x for x in self.PATH.split("/") if x != ""]
        self.queue = (
            self.parse_input(an_input="/".join(queue))
            if (queue and self.PATH != "/")
            else list()
        )

        controller_choices = self.CHOICES_COMMANDS + self.CHOICES_MENUS
        if controller_choices:
            self.controller_choices = controller_choices + self.CHOICES_COMMON
        else:
            self.controller_choices = self.CHOICES_COMMON

        self.completer: Union[None, NestedCompleter] = None

        self.parser = argparse.ArgumentParser(
            add_help=False,
            prog=self.path[-1] if self.PATH != "/" else "cli",
        )
        self.parser.exit_on_error = False  # type: ignore
        self.parser.add_argument("cmd", choices=self.controller_choices)

    def check_path(self) -> None:
        """Check if command path is valid."""
        path = self.PATH
        if path[0] != "/":
            raise ValueError("Path must begin with a '/' character.")
        if path[-1] != "/":
            raise ValueError("Path must end with a '/' character.")
        if not re.match("^[a-z/]*$", path):
            raise ValueError(
                "Path must only contain lowercase letters and '/' characters."
            )

    def load_class(self, class_ins, *args, **kwargs):
        """Check for an existing instance of the controller before creating a new one."""
        settings = Session().settings
        self.save_class()
        arguments = len(args) + len(kwargs)
        # Due to the 'arguments == 1' condition, we actually NEVER load a class
        # that has arguments (The 1 argument corresponds to self.queue)
        # Advantage: If the user changes something on one controller and then goes to the
        # controller below, it will create such class from scratch bringing all new variables
        # in and considering latest changes.
        # Disadvantage: If the user goes on a controller below and we have been there before
        # it will not load that previous class, but create a new one from scratch.
        # SCENARIO: If the user is in stocks and does load AAPL/ta the TA menu will get AAPL,
        # and if then the user goes back to the stocks menu using .. that menu will have AAPL
        # Now, if "arguments == 1" condition exists, if the user does "load TSLA" and then
        # goes into "TA", the "TSLA" ticker will appear. If that condition doesn't exist
        # the previous class will be loaded and even if the user changes the ticker on
        # the stocks context it will not impact the one of TA menu - unless changes are done.
        if (
            class_ins.PATH in controllers
            and arguments == 1
            and settings.REMEMBER_CONTEXTS
        ):
            old_class = controllers[class_ins.PATH]
            old_class.queue = self.queue
            return old_class.menu()
        return class_ins(*args, **kwargs).menu()

    def call_hold(self, other_args: List[str]) -> None:
        """Process hold command."""
        self.save_class()
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="hold",
            description="Turn on figure holding.  This will stop showing images until hold off is run.",
        )
        parser.add_argument(
            "-o",
            "--option",
            choices=["on", "off"],
            type=str,
            default="off",
            dest="option",
        )
        parser.add_argument(
            "-s",
            "--sameaxis",
            action="store_true",
            default=False,
            help="Put plots on the same axis.  Best when numbers are on similar scales",
            dest="axes",
        )
        parser.add_argument(
            "--title",
            type=str,
            default="",
            dest="title",
            nargs="+",
            help="When using hold off, this sets the title for the figure.",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-o")

        ns_parser = self.parse_known_args_and_warn(
            parser,
            other_args,
        )
        if ns_parser:
            if ns_parser.option == "on":
                setup.HOLD = True
                setup.COMMAND_ON_CHART = False
                if ns_parser.axes:
                    setup.set_same_axis()
                else:
                    setup.set_new_axis()
            if ns_parser.option == "off":
                setup.HOLD = False
                if setup.get_current_figure() is not None:
                    # create a subplot
                    fig = setup.get_current_figure()
                    if fig is None:
                        return
                    if not fig.has_subplots and not setup.make_new_axis():
                        fig.set_subplots(1, 1, specs=[[{"secondary_y": True}]])

                    if setup.make_new_axis():
                        for i, trace in enumerate(fig.select_traces()):
                            trace.yaxis = f"y{i+1}"

                            if i != 0:
                                fig.update_layout(
                                    {
                                        f"yaxis{i+1}": dict(
                                            side="left",
                                            overlaying="y",
                                            showgrid=True,
                                            showline=False,
                                            zeroline=False,
                                            automargin=True,
                                            ticksuffix=(
                                                "       " * (i - 1) if i > 1 else ""
                                            ),
                                            tickfont=dict(
                                                size=18,
                                            ),
                                            title=dict(
                                                font=dict(
                                                    size=15,
                                                ),
                                                standoff=0,
                                            ),
                                        ),
                                    }
                                )
                        # pylint: disable=undefined-loop-variable
                        fig.update_layout(margin=dict(l=30 * i))

                    else:
                        fig.update_yaxes(title="")

                    if any(setup.get_legends()):
                        for trace, new_name in zip(
                            fig.select_traces(), setup.get_legends()
                        ):
                            if new_name:
                                trace.name = new_name

                    fig.update_layout(title=" ".join(ns_parser.title))
                    fig.show()
                    setup.COMMAND_ON_CHART = True

                    setup.set_current_figure(None)
                    setup.reset_legend()

    def save_class(self) -> None:
        """Save the current instance of the class to be loaded later."""
        if Session().settings.REMEMBER_CONTEXTS:
            controllers[self.PATH] = self

    def custom_reset(self) -> List[str]:
        """Implement custom reset.

        This will be replaced by any children with custom_reset functions.
        """
        return []

    @abstractmethod
    def print_help(self) -> None:
        """Print help placeholder."""
        raise NotImplementedError("Must override print_help.")

    def parse_input(self, an_input: str) -> list:
        """Parse controller input.

        Splits the command chain from user input into a list of individual commands
        while respecting the forward slash in the command arguments.

        In the default scenario only unix-like paths are handles by the parser.
        Override this function in the controller classes that inherit from this one to
        resolve edge cases specific to command arguments on those controllers.

        When handling edge cases add additional regular expressions to the list.

        Parameters
        ----------
        an_input : str
            User input string

        Returns
        ----------
        list
            Command queue as list
        """
        custom_filters: list = []
        commands = parse_and_split_input(
            an_input=an_input, custom_filters=custom_filters
        )
        return commands

    def switch(self, an_input: str) -> List[str]:
        """Process and dispatch input.

        Returns
        ----------
        List[str]
            list of commands in the queue to execute
        """
        actions = self.parse_input(an_input)

        if an_input and an_input != "reset":
            Session().console.print()

        # Empty command
        if len(actions) == 0:
            pass

        # Navigation slash is being used first split commands
        elif len(actions) > 1:
            # Absolute path is specified
            if not actions[0]:
                actions[0] = "home"

            # Add all instructions to the queue
            for cmd in actions[::-1]:
                if cmd:
                    self.queue.insert(0, cmd)

        # Single command fed, process
        else:
            try:
                (known_args, other_args) = self.parser.parse_known_args(
                    an_input.split()
                )
            except Exception as exc:
                raise SystemExit from exc

            if RECORD_SESSION:
                SESSION_RECORDED.append(an_input)

            # Redirect commands to their correct functions
            if known_args.cmd:
                if known_args.cmd in ("..", "q"):
                    known_args.cmd = "quit"
                elif known_args.cmd in ("e"):
                    known_args.cmd = "exit"
                elif known_args.cmd in ("?", "h"):
                    known_args.cmd = "help"
                elif known_args.cmd == "r":
                    known_args.cmd = "reset"

            getattr(
                self,
                "call_" + known_args.cmd,
                lambda _: "Command not recognized!",
            )(other_args)

        if (
            an_input
            and an_input != "reset"
            and (
                not self.queue or (self.queue and self.queue[0] not in ("quit", "help"))
            )
        ):
            Session().console.print()

        return self.queue

    def call_cls(self, _) -> None:
        """Process cls command."""
        system_clear()

    def call_home(self, _) -> None:
        """Process home command."""
        self.save_class()
        if self.PATH.count("/") == 1 and Session().settings.ENABLE_EXIT_AUTO_HELP:
            self.print_help()
        for _ in range(self.PATH.count("/") - 1):
            self.queue.insert(0, "quit")

    def call_help(self, _) -> None:
        """Process help command."""
        self.print_help()

    def call_quit(self, _) -> None:
        """Process quit menu command."""
        self.save_class()
        self.queue.insert(0, "quit")

    def call_exit(self, _) -> None:
        # Not sure how to handle controller loading here
        """Process exit cli command."""
        self.save_class()
        for _ in range(self.PATH.count("/")):
            self.queue.insert(0, "quit")

        if not Session().is_local():
            remove_file(
                Path(Session().user.preferences.export_directory, "routines", "hub")
            )

    def call_reset(self, _) -> None:
        """Process reset command.

        If you would like to have customization in the reset process define a method
        `custom_reset` in the child class.
        """
        self.save_class()
        if self.PATH != "/":
            if self.custom_reset():
                self.queue = self.custom_reset() + self.queue
            else:
                for val in self.path[::-1]:
                    self.queue.insert(0, val)
            self.queue.insert(0, "reset")
            for _ in range(len(self.path)):
                self.queue.insert(0, "quit")

    def call_record(self, other_args) -> None:
        """Process record command."""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="record",
            description="Start recording session into .openbb routine file",
        )
        parser.add_argument(
            "-n",
            "--name",
            action="store",
            dest="name",
            type=str,
            default="",
            help="Routine title name to be saved - only use characters, digits and whitespaces.",
            nargs="+",
        )
        parser.add_argument(
            "-d",
            "--description",
            type=str,
            dest="description",
            help="The description of the routine",
            default=f"Routine recorded at {datetime.now().strftime('%H:%M')} from the OpenBB Platform CLI",
            nargs="+",
        )
        parser.add_argument(
            "--tag1",
            type=str,
            dest="tag1",
            help=f"The tag associated with the routine. Select from: {', '.join(SCRIPT_TAGS)}",
            default="",
            nargs="+",
        )
        parser.add_argument(
            "--tag2",
            type=str,
            dest="tag2",
            help=f"The tag associated with the routine. Select from: {', '.join(SCRIPT_TAGS)}",
            default="",
            nargs="+",
        )
        parser.add_argument(
            "--tag3",
            type=str,
            dest="tag3",
            help=f"The tag associated with the routine. Select from: {', '.join(SCRIPT_TAGS)}",
            default="",
            nargs="+",
        )
        parser.add_argument(
            "-p",
            "--public",
            dest="public",
            action="store_true",
            help="Whether the routine should be public or not",
            default=False,
        )
        parser.add_argument(
            "-l",
            "--local",
            dest="local",
            action="store_true",
            help="Only save the routine locally - this is necessary if you are running in guest mode.",
            default=False,
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-n")

        ns_parser = self.parse_simple_args(parser, other_args)

        if ns_parser:
            if not ns_parser.name:
                Session().console.print(
                    "[red]Set a routine title by using the '-n' flag. E.g. 'record -n Morning routine'[/red]"
                )
                return

            tag1 = (
                " ".join(ns_parser.tag1)
                if isinstance(ns_parser.tag1, list)
                else ns_parser.tag1
            )
            if tag1 and tag1 not in SCRIPT_TAGS:
                Session().console.print(
                    f"[red]The parameter 'tag1' needs to be one of the following {', '.join(SCRIPT_TAGS)}[/red]"
                )
                return

            tag2 = (
                " ".join(ns_parser.tag2)
                if isinstance(ns_parser.tag2, list)
                else ns_parser.tag2
            )
            if tag2 and tag2 not in SCRIPT_TAGS:
                Session().console.print(
                    f"[red]The parameter 'tag2' needs to be one of the following {', '.join(SCRIPT_TAGS)}[/red]"
                )
                return

            tag3 = (
                " ".join(ns_parser.tag3)
                if isinstance(ns_parser.tag3, list)
                else ns_parser.tag3
            )
            if tag3 and tag3 not in SCRIPT_TAGS:
                Session().console.print(
                    f"[red]The parameter 'tag3' needs to be one of the following {', '.join(SCRIPT_TAGS)}[/red]"
                )
                return

            if Session().is_local() and not ns_parser.local:
                Session().console.print(
                    "[red]Recording session to the OpenBB Hub is not supported in guest mode.[/red]"
                )
                Session().console.print(
                    "\n[yellow]Sign to OpenBB Hub to register: http://openbb.co[/yellow]"
                )
                Session().console.print(
                    "\n[yellow]Otherwise set the flag '-l' to save the file locally.[/yellow]"
                )
                return

            # Check if title has a valid format
            title = " ".join(ns_parser.name) if ns_parser.name else ""
            pattern = re.compile(r"^[a-zA-Z0-9\s]+$")
            if not pattern.match(title):
                Session().console.print(
                    f"[red]Title '{title}' has invalid format. Please use only digits, characters and whitespaces.[/]"
                )
                return

            global RECORD_SESSION  # noqa: PLW0603
            global RECORD_SESSION_LOCAL_ONLY  # noqa: PLW0603
            global SESSION_RECORDED_NAME  # noqa: PLW0603
            global SESSION_RECORDED_DESCRIPTION  # noqa: PLW0603
            global SESSION_RECORDED_TAGS  # noqa: PLW0603
            global SESSION_RECORDED_PUBLIC  # noqa: PLW0603

            RECORD_SESSION = True
            RECORD_SESSION_LOCAL_ONLY = ns_parser.local
            SESSION_RECORDED_NAME = title
            SESSION_RECORDED_DESCRIPTION = (
                " ".join(ns_parser.description)
                if isinstance(ns_parser.description, list)
                else ns_parser.description
            )
            SESSION_RECORDED_TAGS = tag1 if tag1 else ""
            SESSION_RECORDED_TAGS += "," + tag2 if tag2 else ""
            SESSION_RECORDED_TAGS += "," + tag3 if tag3 else ""

            SESSION_RECORDED_PUBLIC = ns_parser.public

            Session().console.print(
                f"[green]The routine '{title}' is successfully being recorded.[/green]"
            )
            Session().console.print(
                "\n[yellow]Remember to run 'stop' command when you are done!\n[/yellow]"
            )

    def call_stop(self, _) -> None:
        """Process stop command."""
        global RECORD_SESSION  # noqa: PLW0603
        global SESSION_RECORDED  # noqa: PLW0603

        if not RECORD_SESSION:
            Session().console.print(
                "[red]There is no session being recorded. Start one using the command 'record'[/red]\n"
            )
        elif len(SESSION_RECORDED) < 5:
            Session().console.print(
                "[red]Run at least 4 commands before stopping recording a session.[/red]\n"
            )
        else:
            current_user = Session().user

            # Check if the user just wants to store routine locally
            # This works regardless of whether they are logged in or not
            if RECORD_SESSION_LOCAL_ONLY:
                # Whitespaces are replaced by underscores and an .openbb extension is added
                title_for_local_storage = (
                    SESSION_RECORDED_NAME.replace(" ", "_") + ".openbb"
                )

                routine_file = os.path.join(
                    f"{current_user.preferences.export_directory}/routines",
                    title_for_local_storage,
                )

                # If file already exists, add a timestamp to the name
                if os.path.isfile(routine_file):
                    i = Session().console.input(
                        "A local routine with the same name already exists, "
                        "do you want to override it? (y/n): "
                    )
                    Session().console.print("")
                    while i.lower() not in ["y", "yes", "n", "no"]:
                        i = Session().console.input("Select 'y' or 'n' to proceed: ")
                        Session().console.print("")

                    if i.lower() in ["n", "no"]:
                        new_name = (
                            datetime.now().strftime("%Y%m%d_%H%M%S_")
                            + title_for_local_storage
                        )
                        routine_file = os.path.join(
                            current_user.preferences.export_directory,
                            "routines",
                            new_name,
                        )
                        Session().console.print(
                            f"[yellow]The routine name has been updated to '{new_name}'[/yellow]\n"
                        )

                # Writing to file
                Path(os.path.dirname(routine_file)).mkdir(parents=True, exist_ok=True)

                with open(routine_file, "w") as file1:
                    lines = ["# OpenBB Platform CLI - Routine", "\n"]

                    username = getattr(
                        Session().user.profile.hub_session, "username", "local"
                    )

                    lines += [f"# Author: {username}", "\n\n"] if username else ["\n"]
                    lines += [
                        f"# Title: {SESSION_RECORDED_NAME}",
                        "\n",
                        f"# Tags: {SESSION_RECORDED_TAGS}",
                        "\n\n",
                        f"# Description: {SESSION_RECORDED_DESCRIPTION}",
                        "\n\n",
                    ]
                    lines += [c + "\n" for c in SESSION_RECORDED[:-1]]
                    # Writing data to a file
                    file1.writelines(lines)

                Session().console.print(
                    f"[green]Your routine has been recorded and saved here: {routine_file}[/green]\n"
                )

            # If user doesn't specify they want to store routine locally
            # Confirm that the user is logged in
            elif not Session().is_local():
                routine = "\n".join(SESSION_RECORDED[:-1])
                hub_session = current_user.profile.hub_session

                if routine is not None:
                    auth_header = (
                        f"{hub_session.token_type} {hub_session.access_token.get_secret_value()}"
                        if hub_session
                        else None
                    )
                    kwargs = {
                        "auth_header": auth_header,
                        "name": SESSION_RECORDED_NAME,
                        "description": SESSION_RECORDED_DESCRIPTION,
                        "routine": routine,
                        "tags": SESSION_RECORDED_TAGS,
                        "public": SESSION_RECORDED_PUBLIC,
                    }
                    response = upload_routine(**kwargs)  # type: ignore
                    if response is not None and response.status_code == 409:
                        i = Session().console.input(
                            "A routine with the same name already exists, "
                            "do you want to replace it? (y/n): "
                        )
                        Session().console.print("")
                        if i.lower() in ["y", "yes"]:
                            kwargs["override"] = True  # type: ignore
                            response = upload_routine(**kwargs)  # type: ignore
                        else:
                            Session().console.print("[info]Aborted.[/info]")

            # Clear session to be recorded again
            RECORD_SESSION = False
            SESSION_RECORDED = list()

    def call_whoami(self, other_args: List[str]) -> None:
        """Process whoami command."""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="whoami",
            description="Show current user",
        )
        ns_parser = self.parse_simple_args(parser, other_args)

        if ns_parser:
            current_user = Session().user
            local_user = Session().is_local()
            if not local_user:
                hub_session = current_user.profile.hub_session
                Session().console.print(
                    f"[info]email:[/info] {hub_session.email if hub_session else 'N/A'}"
                )
                Session().console.print(
                    f"[info]uuid:[/info] {hub_session.user_uuid if hub_session else 'N/A'}"
                )
            else:
                print_guest_block_msg()

    @staticmethod
    def parse_simple_args(parser: argparse.ArgumentParser, other_args: List[str]):
        """Parse list of arguments into the supplied parser.

        Parameters
        ----------
        parser: argparse.ArgumentParser
            Parser with predefined arguments
        other_args: List[str]
            List of arguments to parse

        Returns
        -------
        ns_parser:
            Namespace with parsed arguments
        """
        parser.add_argument(
            "-h", "--help", action="store_true", help="show this help message"
        )

        if Session().settings.USE_CLEAR_AFTER_CMD:
            system_clear()

        try:
            (ns_parser, l_unknown_args) = parser.parse_known_args(other_args)
        except SystemExit:
            # In case the command has required argument that isn't specified
            Session().console.print("\n")
            return None

        if ns_parser.help:
            txt_help = parser.format_help()
            Session().console.print(f"[help]{txt_help}[/help]")
            return None

        if l_unknown_args:
            Session().console.print(
                f"The following args couldn't be interpreted: {l_unknown_args}\n"
            )

        return ns_parser

    @classmethod
    def parse_known_args_and_warn(
        cls,
        parser: argparse.ArgumentParser,
        other_args: List[str],
        export_allowed: Literal[
            "no_export", "raw_data_only", "figures_only", "raw_data_and_figures"
        ] = "no_export",
        raw: bool = False,
        limit: int = 0,
    ):
        """Parse list of arguments into the supplied parser.

        Parameters
        ----------
        parser: argparse.ArgumentParser
            Parser with predefined arguments
        other_args: List[str]
            list of arguments to parse
        export_allowed: Literal["no_export", "raw_data_only", "figures_only", "raw_data_and_figures"]
            Export options
        raw: bool
            Add the --raw flag
        limit: int
            Add a --limit flag with this number default

        Returns
        ----------
        ns_parser:
            Namespace with parsed arguments
        """
        parser.add_argument(
            "-h", "--help", action="store_true", help="show this help message"
        )

        if setup.HOLD:
            parser.add_argument(
                "--legend",
                type=str,
                dest="hold_legend_str",
                default="",
                nargs="+",
                help="Label for legend when hold is on.",
            )

        if export_allowed != "no_export":
            choices_export = []
            help_export = "Does not export!"

            if export_allowed == "raw_data_only":
                choices_export = ["csv", "json", "xlsx"]
                help_export = "Export raw data into csv, json, xlsx"
            elif export_allowed == "figures_only":
                choices_export = ["png", "jpg", "pdf", "svg"]
                help_export = "Export figure into png, jpg, pdf, svg "
            else:
                choices_export = ["csv", "json", "xlsx", "png", "jpg", "pdf", "svg"]
                help_export = "Export raw data into csv, json, xlsx and figure into png, jpg, pdf, svg "

            parser.add_argument(
                "--export",
                default="",
                type=check_file_type_saved(choices_export),
                dest="export",
                help=help_export,
            )

            # If excel is an option, add the sheet name
            if export_allowed in [
                "raw_data_only",
                "raw_data_and_figures",
            ]:
                parser.add_argument(
                    "--sheet-name",
                    dest="sheet_name",
                    default=None,
                    nargs="+",
                    help="Name of excel sheet to save data to. Only valid for .xlsx files.",
                )

        if raw:
            parser.add_argument(
                "--raw",
                dest="raw",
                action="store_true",
                default=False,
                help="Flag to display raw data",
            )
        if limit > 0:
            parser.add_argument(
                "-l",
                "--limit",
                dest="limit",
                default=limit,
                help="Number of entries to show in data.",
                type=check_positive,
            )
        if Session().settings.USE_CLEAR_AFTER_CMD:
            system_clear()

        if "--help" in other_args or "-h" in other_args:
            txt_help = parser.format_help() + "\n"
            if parser.prog != "about":
                txt_help += (
                    f"For more information and examples, use 'about {parser.prog}' "
                    f"to access the related guide.\n"
                )
            Session().console.print(f"[help]{txt_help}[/help]")
            return None

        try:
            # If the user uses a comma separated list of arguments, split them
            for index, arg in enumerate(other_args):
                if "," in arg:
                    parts = arg.split(",")
                    other_args[index : index + 1] = parts

            (ns_parser, l_unknown_args) = parser.parse_known_args(other_args)

            if export_allowed in [
                "raw_data_only",
                "raw_data_and_figures",
            ]:
                ns_parser.is_image = any(
                    ext in ns_parser.export for ext in ["png", "svg", "jpg", "pdf"]
                )

        except SystemExit:
            # In case the command has required argument that isn't specified

            return None

        # This protects against the hidden loads in stocks/fa
        if parser.prog != "load" and setup.HOLD:
            setup.set_last_legend(" ".join(ns_parser.hold_legend_str))

        if l_unknown_args:
            Session().console.print(
                f"The following args couldn't be interpreted: {l_unknown_args}"
            )
        return ns_parser

    def menu(self, custom_path_menu_above: str = ""):
        """Enter controller menu."""
        settings = Session().settings
        an_input = "HELP_ME"

        while True:
            # There is a command in the queue
            if self.queue and len(self.queue) > 0:
                if self.queue[0] in ("q", "..", "quit"):
                    self.save_class()
                    # Go back to the root in order to go to the right directory because
                    # there was a jump between indirect menus
                    if custom_path_menu_above:
                        self.queue.insert(1, custom_path_menu_above)

                    if len(self.queue) > 1:
                        return self.queue[1:]

                    if settings.ENABLE_EXIT_AUTO_HELP:
                        return ["help"]
                    return []

                # Consume 1 element from the queue
                an_input = self.queue[0]
                self.queue = self.queue[1:]

                # Print location because this was an instruction and we want user to know the action
                if (
                    an_input
                    and an_input != "home"
                    and an_input != "help"
                    and an_input.split(" ")[0] in self.controller_choices
                ):
                    Session().console.print(
                        f"{get_flair_and_username()} {self.PATH} $ {an_input}"
                    )

            # Get input command from user
            else:
                # Display help menu when entering on this menu from a level above
                if an_input == "HELP_ME":
                    self.print_help()

                try:
                    prompt_session = Session().prompt_session
                    if prompt_session and settings.USE_PROMPT_TOOLKIT:
                        # Check if toolbar hint was enabled
                        if settings.TOOLBAR_HINT:
                            an_input = prompt_session.prompt(
                                f"{get_flair_and_username()} {self.PATH} $ ",
                                completer=self.completer,
                                search_ignore_case=True,
                                bottom_toolbar=HTML(
                                    '<style bg="ansiblack" fg="ansiwhite">[h]</style> help menu    '
                                    '<style bg="ansiblack" fg="ansiwhite">[q]</style> return to previous menu    '
                                    '<style bg="ansiblack" fg="ansiwhite">[e]</style> exit the program    '
                                    '<style bg="ansiblack" fg="ansiwhite">[cmd -h]</style> '
                                    "see usage and available options    "
                                    f'<style bg="ansiblack" fg="ansiwhite">[about (cmd/menu)]</style> '
                                    f"{self.path[-1].capitalize()} (cmd/menu) Documentation"
                                ),
                                style=Style.from_dict(
                                    {"bottom-toolbar": "#ffffff bg:#333333"}
                                ),
                            )
                        else:
                            an_input = prompt_session.prompt(
                                f"{get_flair_and_username()} {self.PATH} $ ",
                                completer=self.completer,
                                search_ignore_case=True,
                            )
                    # Get input from user without auto-completion
                    else:
                        an_input = input(f"{get_flair_and_username()} {self.PATH} $ ")

                except (KeyboardInterrupt, EOFError):
                    # Exit in case of keyboard interrupt
                    an_input = "exit"

            try:
                # Allow user to go back to root
                an_input = "home" if an_input == "/" else an_input

                # Process the input command
                self.queue = self.switch(an_input)

            except SystemExit:
                Session().console.print(
                    f"[red]The command '{an_input}' doesn't exist on the {self.PATH} menu.[/red]\n",
                )
                similar_cmd = difflib.get_close_matches(
                    an_input.split(" ")[0] if " " in an_input else an_input,
                    self.controller_choices,
                    n=1,
                    cutoff=0.7,
                )
                if similar_cmd:
                    if " " in an_input:
                        candidate_input = (
                            f"{similar_cmd[0]} {' '.join(an_input.split(' ')[1:])}"
                        )
                        if candidate_input == an_input:
                            an_input = ""
                            self.queue = []
                            Session().console.print("\n")
                            continue

                        an_input = candidate_input
                    else:
                        an_input = similar_cmd[0]

                    Session().console.print(
                        f"[green]Replacing by '{an_input}'.[/green]\n"
                    )
                    self.queue.insert(0, an_input)
