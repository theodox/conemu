# conemu
Print color terminal codes to ConEmu (http://conemu.github.io/) or other ANSI style terminals


## installation

This is a single-file python module; drop it somewhere in your module paths.

## usage

In ordinary usage you simply import the module. To turn off the console coloring, use `conemu.unset_terminal()`.  Its unlikely you'll ever want to import this module in any other circumstance than running a python session inside ConEmu.

## logging

By default importing conemu creates a logger (called, amazingly, 'conemu') which is color aware. So you can log messages in color like so:

    import logging
    con = logging.getLogger('conemu')
    con.warn("Color log warning")

You can also override the default logger, making it color aware, by calling `conemu.override_default_logger(fmt, datefmt)`. This will clear out all handlers on the root logger, so if you have anything fancy going on (such as an automatic file logger) you may lose it -- use with care.


## more

Some more detail and examples [here](http://techartsurvival.blogspot.com/2015/04/goddamit-stop-messing-around.html)
