## About

This is an addon for [qToggleServer](https://github.com/qtoggle/qtoggleserver).

It provides a driver for ports whose values are backed by system commands.


## Install

Install using pip:

    pip install qtoggleserver-cmdline


## Usage

##### `qtoggleserver.conf:`
``` ini
...
peripherals = [
    ...
    {
        driver = "qtoggleserver.cmdline.CommandLine"
        name = "my_command"
        output_regexp = "^some (value1) and some other (value2)$"
        read_command = "/path/to/command with args"
        write_command = "echo ${my_port1} ${my_port2}"
        ports = [
            {id = "my_port1", type = "boolean"}
            {id = "my_port2", type = "number"}
            ...
        ]
        port = {
            id = "my_port"
            type = "boolean"
        }
        timeout = 5
    },
    ...
]
...
```

`name` is an optional name that will be used as a prefix for all ports.

`read_command` sets a command to be executed to determine the value of ports. If this parameter is not specified, no
polling is done and the values will only be set to what is written to the ports.

If `output_regexp` is specified, output of `read_command` is parsed against it as a regular expression. Following rules
apply:

 * If output does not match the regular expression, all port values will be set to `null`.
 * The port values will be determined in order of the indicated groups. If no group is defined, the entire output will
be used to determine the value of all ports.
 * For boolean ports, text `true` (case-insensitive) or any other non-zero decimal number represents `true`.
 * For number ports, matched group content will be converted to float. 

If `output_regexp` is not specified, exit code of `read_command` will be used to determine port values. An exit code of
`0` represents `true` for all boolean ports, while any other exit code represents `false`. All number ports will use
exit code as their value.

The `write_command` parameter, if specified, sets a command that will be called whenever the port value changes. The new
port values will be supplied in environment variables with names corresponding to port ids. Any dots in port ids will be
converted to underscores. Boolean values will be transmitted as `0` and `1`. All port values will be available,
regardless of which one has changed.

If `write_command` is not specified, all ports will be read-only.

`ports` is a list of ports to be exposed. If you only need one port, use the `port` shortcut parameter.

Use the `timeout` parameter to set a timeout when waiting for the commands to complete, in seconds.

Although using blocking commands will not block the server, it is recommended that you supply commands that don't block.
