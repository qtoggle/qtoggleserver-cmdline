
import asyncio
import logging
import re

from typing import Any, Dict, List, Optional, Tuple

from qtoggleserver.core import ports as core_ports
from qtoggleserver.core.typing import NullablePortValue, PortValue
from qtoggleserver.lib import polled

from .exceptions import CommandTimeout
from .. import cmdline


class CommandLine(polled.PolledPeripheral):
    DEFAULT_POLL_INTERVAL = 10
    RETRY_POLL_INTERVAL = 5
    DEFAULT_TIMEOUT = 5

    logger = logging.getLogger(cmdline.__name__)

    def __init__(
        self,
        *,
        output_regexp: Optional[str] = None,
        read_command: str,
        write_command: Optional[str] = None,
        ports: List[Dict[str, Any]] = None,
        port: Dict[str, Any] = None,
        timeout: int = DEFAULT_TIMEOUT,
        **kwargs
    ) -> None:

        super().__init__(**kwargs)

        self._output_regexp: Optional[re.Pattern] = None
        self._read_command: str = read_command
        self._write_command: Optional[str] = write_command
        self._port_details: List[Dict[str, Any]] = ports
        self._timeout: int = timeout

        if port and not ports:
            self._port_details = [port]

        if output_regexp:
            self._output_regexp = re.compile(output_regexp, re.MULTILINE | re.DOTALL)

        self._values: Dict[str, Optional[float]] = {p['id']: None for p in self._port_details}

    async def run_command(self, cmd: str, env: Optional[Dict[str, str]]) -> Tuple[str, int]:
        self.debug('executing command "%s"', cmd)

        p = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )

        try:
            stdout, stderr = await asyncio.wait_for(p.communicate(), timeout=self._timeout)

        except asyncio.TimeoutError:
            raise CommandTimeout()

        if stderr:
            stderr = stderr.decode().strip()
            stderr = stderr.replace('\n', '\\n')
            self.warning('command returned stderr: %s', stderr)

        stdout = stdout.decode().strip()

        return stdout, p.returncode

    async def poll(self) -> None:
        output, exit_code = await self.run_command(self._read_command, env=None)

        if self._output_regexp:
            m = self._output_regexp.match(output)
            if not m:
                # If output doesn't match our regexp, use None for all values
                for k in self._values:
                    self._values[k] = None

                return

            groups = list(m.groups())
            if not groups:
                groups = [output] * len(self._port_details)

            while len(groups) < len(self._port_details):
                groups.append('')

            for i, p in enumerate(self._port_details):
                g = groups[i].strip().lower()
                try:
                    value = int(g)

                except ValueError:
                    try:
                        value = float(g)

                    except ValueError:
                        value = None

                if (p['type'] == core_ports.TYPE_BOOLEAN) and (value is None):
                    value = int(g == 'true')  # For boolean ports, text "true" is also accepted

                self._values[p['id']] = value

        else:
            # When no regexp is given, use exit code
            for i, k in enumerate(self._values):
                if self._port_details[i]['type'] == core_ports.TYPE_BOOLEAN:
                    self._values[k] = int(not exit_code)  # process exit code 0 means true

                else:
                    self._values[k] = exit_code

    def get_value(self, port_id: str) -> NullablePortValue:
        return self._values.get(port_id)

    def update_value(self, port_id: str, value: PortValue) -> None:
        if isinstance(value, bool):
            value = int(value)  # Keep only int/float values

        self._values[port_id] = value

    async def write_values(self) -> None:
        env = {}
        for port_id, value in self._values.items():
            if value is None:
                value = ''

            else:
                value = str(value)

            port_id = re.sub('[^a-zA-Z0-9_]', '_', port_id)
            env[port_id] = value

        _, exit_code = await self.run_command(self._write_command, env=env)

        if exit_code:
            self.warning('command returned non-zero exit code %d', exit_code)

        # Poll values immediately after writing
        await self.poll()

    async def make_port_args(self) -> List[Dict[str, Any]]:
        from .ports import CommandLinePort

        return [{
            'driver': CommandLinePort,
            'port_id': p['id'],
            'port_type': p['type'],
            'writable': self._write_command is not None
        } for p in self._port_details]
