
class CommandLineException(Exception):
    pass


class CommandTimeout(CommandLineException):
    def __init__(self) -> None:
        super().__init__('Timeout waiting for command to complete')
