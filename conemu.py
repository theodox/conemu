__author__ = 'Stephen Theodore'
from collections import namedtuple
import pprint
import sys
import re
import traceback
import logging


# constants
ESC = '\033'
BELL = '\x07'

# one-off code
code = lambda c: "%s[%im" % (ESC, c)
# 3-part semicolon separated code for (eg) color
multicode = lambda n, i, d: "{}[{};{};{};m".format(ESC, n, i, d)

RESET = code(0)
BOLD = code(1)
INVERSE = code(4)
NOCOLOR = code(39)
NOBG = code(49)
CLEAR = code(23)
CLEAR_SCREEN = ESC + "[2J"

_span = namedtuple('span', 'start end')


class Span(_span):
    '''
    Callable class that spits out start-<string>-end sequence. Create span objects and call them to produce tagged spans.
    '''

    def __call__(self, val):
        return "{}{}{}".format(self.start, val, self.end)


class Terminal(object):
    '''
    A namespace containing generic terminal formatting
    
    There is no need to instantiate this: its just a collection of functions under a name.
    '''
    color = tuple((Span(multicode(38, 5, c), NOCOLOR)) for c in range(16))
    bg = tuple((Span(multicode(48, 5, c), NOBG)) for c in range(7))
    reverse = Span(INVERSE, RESET)
    bold = Span(BOLD, RESET)
    reset = RESET

    @classmethod
    def set_prompt(cls, prompt, prompt2=".", color=color[8]):
        """
        Set the system prompt, and set the continuation prompt to the same width.  If color
        is supplied, color the system prompt with it.
        """
        sys.ps1 = color(prompt)
        sys.ps2 = color((prompt2 * (len(prompt) - 1)) + " ")

    @classmethod
    def unset_prompt(cls):
        """
        Revert to standard python prompts
        """
        sys.ps1 = ">>> "
        sys.ps2 = "... "

    @classmethod
    def clear(cls):
        """
        Clear the terminal screen

        @note : I'm not sure it this works on ANSI terminals other than ConEmu.
        """
        sys.__stdout__.write(CLEAR_SCREEN)


class ConEmu(object):
    '''
    ConEmu-specific format commands
    
    There is no need to instantiate this: its just a collection of functions under a name.
    '''
    CONEMU = ESC + ']9;{};{}' + BELL

    @classmethod
    def alert(cls, msg):
        sys.__stdout__.writelines(cls.CONEMU.format(2, msg))

    @classmethod
    def set_title(cls, msg):
        sys.__stdout__.writelines(cls.CONEMU.format(1, msg))

    @classmethod
    def set_tab(cls, msg):
        sys.__stdout__.writelines(cls.CONEMU.format(3, msg))

    @classmethod
    def progress(cls, active, progress):
        _st = "1;" if active else "0;"
        _pg = str(int(progress))
        sys.__stdout__.writelines(cls.CONEMU.format(4, _st + _pg))


class ErrorWriter(object):
    """
    Format sys.stderr for use with Maya
    """

    TEXT = Terminal.color[8]
    BG = Terminal.bg[1]


    def __init__(self, color=TEXT, bg=BG):
        self.color = color
        self.bg = bg

    def write(self, arg):
        sys.__stderr__.write(self.color(self.bg(arg)))

    def writelines(self, *arg):
        sys.__stderr__.writelines(self.color(self.bg("\n".join(arg))))

    def excepthook(self, tb_type, exc_object, tb, detail=2):
        result = traceback.format_exception(tb_type, exc_object, tb, detail)
        header = '_' * 80
        padded = lambda p: p[:-1].ljust(80)
        # ignore the 'traceback' line
        if result[0].startswith('Traceback'):
            result = result[1:]
        result = [header] + result
        final = map(padded, result)
        self.writelines('\n'.join(final) + "\n")


class MayaWriter(object):
    """
    Formats sys.stdout for use with Maya
    """

    GENERIC = Terminal.color[15]  # for generic printouts
    COMMENT = Terminal.color[14]  # for code comments
    CODE = Terminal.color[3]  # for code objects
    MAYA = Terminal.color[11]  # for maya objects
    BG = Terminal.bg[0]  # background (none by default)


    def __init__(self, color=GENERIC,
                 bg=BG,
                 comment_color=COMMENT,
                 maya_color=MAYA,
                 code_color=CODE):
        self.color = color
        self.code_color = Span(code_color.start, self.color.start)
        self.comment_color = Span(comment_color.start, self.color.start)
        self.maya_color = Span(maya_color.start, self.color.start)
        self.bg = bg
        self.unicode = re.compile("u'(\S*)'")
        self.comment = re.compile('^[#/].*')
        self.repr_code = re.compile("<.*>")

    def replace_unicode(self, val):
        """
        color Unicode strings with self.maya_color, useful for picking out object namnes
        """
        return self.maya_color(val.group()[1:])

    def replace_comment(self, val):
        """
        color comment strings with self.comment_color
        """
        return self.comment_color(val.group())

    def replace_repr(self, val):
        """
        color repr strings (in angle brackets) with self.code_color
        """
        return self.code_color(val.group())


    def write(self, arg):
        if ":" in arg: arg = "# " + arg
        arg = re.sub(self.unicode, self.replace_unicode, arg)
        arg = re.sub(self.comment, self.replace_comment, arg)
        arg = re.sub(self.repr_code, self.replace_repr, arg)
        sys.__stdout__.write(self.color(self.bg(arg)))

    def writelines(self, *arg):
        sys.__stdout__.writelines(self.color(self.bg("\n".join(arg))))

    def display_hook(self, obj):
        """
        Use prettyprint to clean up display of returned objects. Especially handy for display of things like cmds.ls()
        """
        if obj is not None:
            disp = pprint.pformat(obj, indent=2)
            self.write(disp)
            self.write('\n')


def set_terminal(writer=None, errorwriter=None):
    """
    Override sys.stdout with a MayaWriter (supplied or default) and an ErrorWriter(supplied or default)
    """
    writer = writer or MayaWriter()
    errorwriter = errorwriter or ErrorWriter()

    sys.stderr = errorwriter
    sys.stdout = writer
    sys.displayhook = writer.display_hook
    sys.excepthook = errorwriter.excepthook


def unset_terminal():
    """
    Reset sys.stdout and sys.stderr to default
    """
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    sys.displayhook = sys.__displayhook__
    sys.excepthook = sys.__excepthook__


class ColorLogFormatter(logging.Formatter):
    DEBUG = Terminal.color[6]
    INFO = Terminal.color[13]
    WARN = Terminal.color[11]
    ERROR = Terminal.color[8]
    CRIT = Terminal.color[8]
    ERROR_BG = Terminal.bg[1]


    def __init__(self, fmt=None, datefmt=None, debug=DEBUG, info=INFO, warn=WARN, error=ERROR, crit=CRIT):
        super(ColorLogFormatter, self).__init__(fmt, datefmt)
        self._format = fmt
        self.debug = debug
        self.info = info
        self.warn = warn
        self.error = error
        self.crit = crit
        self._color_choice = {
            logging.INFO: self.info,
            logging.DEBUG: self.DEBUG,
            logging.WARNING: self.warn,
            logging.ERROR: self.error,
            logging.CRITICAL: self.crit
        }
        self.error_bg = self.ERROR_BG

    def format(self, record):
        format_color = self._color_choice[record.levelno]
        if record.levelno > logging.WARNING:
            format_color = lambda p: self.error_bg(self._color_choice[record.levelno](p))

        return format_color(super(ColorLogFormatter, self).format(record))


# automatically set the terminal to <maya> and turn on coloring on import
# if you're not using this with Maya or ConEmu you'll want to edit these lines
set_terminal()
ConEmu.set_tab('MAYA')
Terminal.set_prompt("<maya> ")

# create a color-aware logger named 'conemu'
_color_handler = logging.StreamHandler(sys.stdout)
_color_handler.setFormatter(ColorLogFormatter())
logging.getLogger('conemu').addHandler(_color_handler)
logging.getLogger('conemu').propagate = False


def override_root_logger(fmt=None, datefmt=None):
    """
    Make the root logger color-aware. Note that this will remove any existing
    handlers or formatters on the root logger - use with care
    """
    root = logging.getLogger()
    root.handlers = []
    root_color_handler = logging.StreamHandler(sys.stdout)
    root_color_handler.setFormatter(ColorLogFormatter(fmt, datefmt))
    root.addHandler(root_color_handler)