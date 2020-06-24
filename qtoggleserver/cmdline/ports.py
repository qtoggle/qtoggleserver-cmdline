
from typing import cast

from qtoggleserver.core.typing import NullablePortValue, PortValue
from qtoggleserver.lib import polled

from .peripheral import CommandLine


class CommandLinePort(polled.PolledPort):
    def __init__(self, *, port_id: str, port_type: str, writable: bool, **kwargs) -> None:
        self._port_id: str = port_id
        self._type: str = port_type
        self._writable = writable

        super().__init__(**kwargs)

    def get_peripheral(self) -> CommandLine:
        return cast(CommandLine, super().get_peripheral())

    def make_id(self) -> str:
        return self._port_id

    async def write_value(self, value: PortValue) -> None:
        peripheral = self.get_peripheral()
        peripheral.update_value(self._port_id, value)

        await peripheral.write_values()

    async def read_value(self) -> NullablePortValue:
        value = self.get_peripheral().get_value(self._port_id)
        return await self.adapt_value_type(value)
