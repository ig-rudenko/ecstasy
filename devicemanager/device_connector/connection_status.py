import logging
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from ipaddress import IPv4Address

from devicemanager.device_connector.ssh_host_keys import PendingSSHHostKeyChange, SSHKnownHostsStore
from devicemanager.exceptions import SSHConnectionError

logger = logging.getLogger(__name__)

HOST_KEY_CHANGED_MESSAGE = "HOST IDENTIFICATION HAS CHANGED"
MAX_ERROR_MESSAGE_LENGTH = 2_000


class ConnectionStatusStore:
    """Thread-safe in-memory diagnostics for device connections."""

    def __init__(
        self,
        host_key_store: SSHKnownHostsStore | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        """Initialize the store and injectable system dependencies."""

        self._host_key_store = host_key_store or SSHKnownHostsStore()
        self._now = now or (lambda: datetime.now(UTC))
        self._errors: dict[str, dict[str, str]] = {}
        self._ssh_host_key_changes: dict[str, PendingSSHHostKeyChange] = {}
        self._lock = threading.RLock()

    def record_error(self, ip: str, error: Exception, ssh_port: int) -> None:
        """Store the latest error and inspect a changed SSH host key."""

        valid_ip = IPv4Address(ip).compressed
        occurred_at = self._now()
        error_status = {
            "type": error.__class__.__name__,
            "message": str(error)[:MAX_ERROR_MESSAGE_LENGTH],
            "occurredAt": occurred_at.isoformat(),
        }
        pending_change = None
        if HOST_KEY_CHANGED_MESSAGE in str(error):
            try:
                pending_change = self._host_key_store.inspect(valid_ip, ssh_port, occurred_at)
            except Exception as inspect_error:  # noqa: BLE001 - diagnostics must not hide the original error.
                ssh_output = error.ssh_output if isinstance(error, SSHConnectionError) else ""
                if ssh_output:
                    try:
                        pending_change = self._host_key_store.inspect_warning(
                            valid_ip,
                            ssh_port,
                            occurred_at,
                            ssh_output,
                        )
                    except Exception as warning_error:  # noqa: BLE001 - keep the original connection error.
                        logger.error(
                            "Device: %s | Не удалось получить изменившийся SSH host key",
                            valid_ip,
                            exc_info=warning_error,
                        )
                else:
                    logger.error(
                        "Device: %s | Не удалось получить изменившийся SSH host key",
                        valid_ip,
                        exc_info=inspect_error,
                    )

        with self._lock:
            self._errors[valid_ip] = error_status
            if pending_change is not None:
                self._ssh_host_key_changes[valid_ip] = pending_change

    def record_success(self, ip: str) -> None:
        """Clear stale diagnostics after a successful device request."""

        valid_ip = IPv4Address(ip).compressed
        with self._lock:
            self._errors.pop(valid_ip, None)
            self._ssh_host_key_changes.pop(valid_ip, None)

    def get_status(self, ip: str) -> dict[str, object]:
        """Return the latest safe diagnostics for one device."""

        valid_ip = IPv4Address(ip).compressed
        with self._lock:
            error = self._errors.get(valid_ip)
            pending_change = self._ssh_host_key_changes.get(valid_ip)
            return {
                "error": dict(error) if error is not None else None,
                "sshHostKeyChange": pending_change.as_dict() if pending_change is not None else None,
            }

    def confirm_ssh_host_key(self, ip: str) -> bool:
        """Apply a pending key and clear diagnostics after successful confirmation."""

        valid_ip = IPv4Address(ip).compressed
        with self._lock:
            pending_change = self._ssh_host_key_changes.get(valid_ip)
            if pending_change is None:
                return False
            self._host_key_store.confirm(pending_change)
            self._errors.pop(valid_ip, None)
            self._ssh_host_key_changes.pop(valid_ip, None)
            return True


CONNECTION_STATUSES = ConnectionStatusStore()
