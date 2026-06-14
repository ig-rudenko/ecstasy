import importlib
import os
import re
import subprocess
import tempfile
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from ipaddress import IPv4Address
from pathlib import Path
from typing import Protocol, cast


class FcntlModule(Protocol):
    """Subset of fcntl used for the Linux known_hosts file lock."""

    LOCK_EX: int
    LOCK_UN: int

    def flock(self, fd: int, operation: int) -> None:
        """Apply or release an advisory file lock."""


fcntl_module: FcntlModule | None
try:
    fcntl_module = cast(FcntlModule, importlib.import_module("fcntl"))
except ImportError:  # pragma: no cover - fcntl is available in the Linux service containers.
    fcntl_module = None

KNOWN_HOSTS_THREAD_LOCK = threading.RLock()


@dataclass(frozen=True)
class SSHKeyInfo:
    """Public information about one SSH host key."""

    type: str
    fingerprint: str

    def as_dict(self) -> dict[str, str]:
        """Return the frontend API representation."""

        return {"type": self.type, "fingerprint": self.fingerprint}


@dataclass(frozen=True)
class PendingSSHHostKeyChange:
    """A scanned SSH host key change waiting for staff confirmation."""

    ip: str
    port: int
    detected_at: datetime
    previous_keys: tuple[SSHKeyInfo, ...]
    new_keys: tuple[SSHKeyInfo, ...]
    new_key_lines: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        """Return the safe public part of the pending change."""

        return {
            "detectedAt": self.detected_at.isoformat(),
            "port": self.port,
            "previousKeys": [key.as_dict() for key in self.previous_keys],
            "newKeys": [key.as_dict() for key in self.new_keys],
        }


class SSHKnownHostsStore:
    """Inspect and update the OpenSSH known_hosts file."""

    def __init__(self, known_hosts_path: Path | None = None) -> None:
        """Use the current service user's known_hosts file by default."""

        self.known_hosts_path = known_hosts_path or Path.home() / ".ssh" / "known_hosts"

    @staticmethod
    def _host(ip: str, port: int) -> str:
        """Return the OpenSSH known_hosts host identifier."""

        valid_ip = IPv4Address(ip).compressed
        if not 1 <= port <= 65_535:
            raise ValueError("SSH port must be between 1 and 65535")
        return valid_ip if port == 22 else f"[{valid_ip}]:{port}"

    @staticmethod
    def _key_lines(output: str) -> tuple[str, ...]:
        """Extract unique host key lines from OpenSSH command output."""

        lines = []
        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            fields = line.split()
            if len(fields) < 3 or not fields[1].startswith(("ssh-", "ecdsa-", "sk-")):
                continue
            if line not in lines:
                lines.append(line)
        return tuple(lines)

    @staticmethod
    def _fingerprint(key_line: str) -> SSHKeyInfo:
        """Calculate an SHA256 fingerprint for one public host key line."""

        result = subprocess.run(
            ["ssh-keygen", "-lf", "-"],
            input=key_line + "\n",
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        fields = result.stdout.strip().split()
        if len(fields) < 2:
            raise ValueError("ssh-keygen returned an invalid fingerprint")
        key_type = key_line.split()[1]
        return SSHKeyInfo(type=key_type, fingerprint=fields[1])

    def _find_previous_key_lines(self, host: str) -> tuple[str, ...]:
        """Read current keys for a host, including hashed known_hosts entries."""

        if not self.known_hosts_path.exists():
            return ()

        result = subprocess.run(
            ["ssh-keygen", "-F", host, "-f", os.fspath(self.known_hosts_path)],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(result.stderr.strip() or "ssh-keygen failed to read known_hosts")
        return self._key_lines(result.stdout)

    @staticmethod
    def _scan_new_key_lines(ip: str, port: int) -> tuple[str, ...]:
        """Scan the currently presented SSH host keys without trusting them."""

        result = subprocess.run(
            ["ssh-keyscan", "-T", "5", "-p", str(port), ip],
            capture_output=True,
            text=True,
            timeout=7,
            check=False,
        )
        key_lines = SSHKnownHostsStore._key_lines(result.stdout)
        if not key_lines:
            raise RuntimeError(result.stderr.strip() or "ssh-keyscan did not return host keys")
        return key_lines

    def inspect(self, ip: str, port: int, detected_at: datetime) -> PendingSSHHostKeyChange:
        """Read old keys and scan the replacement keys presented by the device."""

        host = self._host(ip, port)
        previous_key_lines = self._find_previous_key_lines(host)
        new_key_lines = self._scan_new_key_lines(ip, port)
        return PendingSSHHostKeyChange(
            ip=IPv4Address(ip).compressed,
            port=port,
            detected_at=detected_at,
            previous_keys=tuple(self._fingerprint(line) for line in previous_key_lines),
            new_keys=tuple(self._fingerprint(line) for line in new_key_lines),
            new_key_lines=new_key_lines,
        )

    def inspect_warning(
        self,
        ip: str,
        port: int,
        detected_at: datetime,
        ssh_output: str,
    ) -> PendingSSHHostKeyChange:
        """Build a pending change from the fingerprint printed by OpenSSH."""

        match = re.search(
            r"The fingerprint for the (?P<type>\S+) key sent by the remote host is\s+"
            r"(?P<fingerprint>SHA256:[A-Za-z0-9+/=]+)",
            ssh_output,
            flags=re.IGNORECASE,
        )
        if match is None:
            raise RuntimeError("OpenSSH warning did not contain the new host key fingerprint")

        host = self._host(ip, port)
        key_type = {
            "dsa": "ssh-dss",
            "ecdsa": "ecdsa",
            "ed25519": "ssh-ed25519",
            "rsa": "ssh-rsa",
        }.get(match.group("type").lower(), match.group("type").lower())
        return PendingSSHHostKeyChange(
            ip=IPv4Address(ip).compressed,
            port=port,
            detected_at=detected_at,
            previous_keys=tuple(self._fingerprint(line) for line in self._find_previous_key_lines(host)),
            new_keys=(SSHKeyInfo(type=key_type, fingerprint=match.group("fingerprint")),),
            new_key_lines=(),
        )

    @contextmanager
    def _locked(self) -> Iterator[None]:
        """Serialize known_hosts updates across threads and Linux service processes."""

        self.known_hosts_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        lock_path = self.known_hosts_path.with_name(f"{self.known_hosts_path.name}.lock")
        with KNOWN_HOSTS_THREAD_LOCK, lock_path.open("a", encoding="utf-8") as lock_file:
            if fcntl_module is not None:
                fcntl_module.flock(lock_file.fileno(), fcntl_module.LOCK_EX)
            try:
                yield
            finally:
                if fcntl_module is not None:
                    fcntl_module.flock(lock_file.fileno(), fcntl_module.LOCK_UN)

    def _confirm(self, change: PendingSSHHostKeyChange) -> None:
        """Replace known_hosts entries while the caller holds the update lock."""

        host = self._host(change.ip, change.port)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".known_hosts.",
            dir=self.known_hosts_path.parent,
            text=True,
        )
        os.close(descriptor)
        temporary_path = Path(temporary_name)
        backup_path = Path(f"{temporary_name}.old")

        try:
            if self.known_hosts_path.exists():
                temporary_path.write_bytes(self.known_hosts_path.read_bytes())
            temporary_path.chmod(0o600)

            remove_result = subprocess.run(
                ["ssh-keygen", "-R", host, "-f", os.fspath(temporary_path)],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if remove_result.returncode not in (0, 1):
                raise RuntimeError(remove_result.stderr.strip() or "ssh-keygen failed to update known_hosts")

            if change.new_key_lines:
                with temporary_path.open("a", encoding="utf-8", newline="\n") as known_hosts_file:
                    known_hosts_file.write("\n".join(change.new_key_lines) + "\n")
                    known_hosts_file.flush()
                    os.fsync(known_hosts_file.fileno())

            os.replace(temporary_path, self.known_hosts_path)
            self.known_hosts_path.chmod(0o600)
        finally:
            temporary_path.unlink(missing_ok=True)
            backup_path.unlink(missing_ok=True)

    def confirm(self, change: PendingSSHHostKeyChange) -> None:
        """Replace known_hosts entries with the exact keys shown for confirmation."""

        with self._locked():
            self._confirm(change)

    def accept_current(self, ip: str, port: int, detected_at: datetime) -> PendingSSHHostKeyChange:
        """Scan and atomically accept the SSH keys currently presented by a host."""

        with self._locked():
            change = self.inspect(ip, port, detected_at)
            self._confirm(change)
        return change

    def accept_changed(
        self,
        ip: str,
        port: int,
        detected_at: datetime,
        ssh_output: str,
    ) -> PendingSSHHostKeyChange:
        """Accept a changed key, falling back to the OpenSSH warning."""

        with self._locked():
            try:
                change = self.inspect(ip, port, detected_at)
            except Exception:
                change = self.inspect_warning(ip, port, detected_at, ssh_output)
            self._confirm(change)
        return change
