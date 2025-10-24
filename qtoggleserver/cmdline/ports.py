from typing import cast

from qtoggleserver.core.ports import skip_write_unavailable
from qtoggleserver.core.typing import NullablePortValue, PortValue
from qtoggleserver.lib import polled

from .peripheral import CommandLine


class CommandLinePort(polled.PolledPort):
    def __init__(self, *, id: str, type: str, writable: bool, **kwargs) -> None:
        self._type = type
        self._writable = writable

        super().__init__(id=id, **kwargs)

    def get_peripheral(self) -> CommandLine:
        return cast(CommandLine, super().get_peripheral())

    @skip_write_unavailable
    async def write_value(self, value: PortValue) -> None:
        peripheral = self.get_peripheral()
        peripheral.update_value(self.get_initial_id(), value)

        await peripheral.write_values()

    async def read_value(self) -> NullablePortValue:
        value = self.get_peripheral().get_value(self.get_initial_id())
        return await self.adapt_value_type(value)
