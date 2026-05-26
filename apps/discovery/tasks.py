from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from celery import shared_task
from django.db import close_old_connections
from django.utils import timezone

from .models import DiscoveryAttempt, DiscoveryCandidate, DiscoveryRun
from .services.dataclasses import DeviceFingerprint, DiscoveryAttemptData
from .services.fingerprint import DeviceFingerprinter
from .services.provisioning import accept_candidate
from .services.reconcile import upsert_candidate
from .services.scanner import build_scan_hosts, preflight_address


@shared_task(bind=True, name="discovery_run_task")
def discovery_run_task(self, run_id: int, networks_override: list[str] | None = None) -> dict:
    """Выполнить auto discovery run в фоне."""

    run = DiscoveryRun.objects.select_related("profile").get(id=run_id)
    profile = run.profile
    counters = {"processed": 0, "found": 0, "created": 0, "skipped": 0, "errors": 0}
    counters_lock = Lock()

    try:
        hosts = build_scan_hosts(networks_override or profile.networks, profile.exclude_ips)
    except ValueError as exc:
        run.status = DiscoveryRun.Status.FAILURE
        run.finished_at = timezone.now()
        run.summary = {"error": str(exc)}
        run.save(update_fields=["status", "finished_at", "summary"])
        raise

    run.task_id = str(self.request.id or run.id)
    run.status = DiscoveryRun.Status.PROGRESS
    run.total = len(hosts)
    run.started_at = timezone.now()
    run.save(update_fields=["task_id", "status", "total", "started_at"])

    if not hosts:
        run.status = DiscoveryRun.Status.SUCCESS
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "finished_at"])
        return build_task_result(run)

    def register_progress() -> None:
        """Обновить прогресс Celery и DiscoveryRun."""

        with counters_lock:
            counters["processed"] += 1
            DiscoveryRun.objects.filter(id=run.id).update(
                processed=counters["processed"],
                found=counters["found"],
                created=counters["created"],
                skipped=counters["skipped"],
                errors=counters["errors"],
            )
            if self.request.id:
                self.update_state(
                    state=DiscoveryRun.Status.PROGRESS,
                    meta={
                        "progress": int(counters["processed"] / max(len(hosts), 1) * 100),
                        "processed": counters["processed"],
                        "total": len(hosts),
                    },
                )

    def add_counter(name: str) -> None:
        """Увеличить счетчик запуска discovery."""

        with counters_lock:
            counters[name] += 1

    def process_ip(ip: str) -> None:
        """Обработать один IP адрес."""

        close_old_connections()
        candidate = None
        try:
            detected_protocols, attempts = preflight_address(
                ip,
                protocols=profile.try_protocols or ["ssh", "telnet"],
                timeout=profile.timeout_seconds,
            )
            if not any(detected_protocols.values()):
                save_attempts(run, None, attempts)
                add_counter("skipped")
                return

            fingerprint, fingerprint_attempts = DeviceFingerprinter(profile, include_cli=True).collect(
                ip,
                detected_protocols,
            )
            attempts.extend(fingerprint_attempts)
            if not fingerprint.has_identity():
                fingerprint = DeviceFingerprint(
                    ip=ip,
                    source=DiscoveryCandidate.Source.TCP,
                    detected_protocols=detected_protocols,
                    raw={"preflight": detected_protocols},
                )

            candidate = upsert_candidate(fingerprint)
            save_attempts(run, candidate, attempts)
            add_counter("found")

            if should_auto_create(profile, candidate, run.dry_run):
                accept_candidate(candidate, profile=profile, collect_interfaces=False)
                add_counter("created")

        except Exception as exc:
            add_counter("errors")
            if candidate is not None:
                candidate.last_error = str(exc)[:500]
                candidate.save(update_fields=["last_error"])
            save_attempts(
                run,
                candidate,
                [
                    DiscoveryAttemptData(
                        ip=ip,
                        method=DiscoveryAttempt.Method.PING,
                        status=DiscoveryAttempt.Status.FAILED,
                        error=str(exc)[:500],
                    )
                ],
            )
        finally:
            register_progress()

    workers_count = max(1, min(profile.max_workers, len(hosts)))
    if workers_count == 1:
        for ip in hosts:
            process_ip(ip)
    else:
        with ThreadPoolExecutor(max_workers=workers_count) as executor:
            futures = [executor.submit(process_ip, ip) for ip in hosts]
            for future in as_completed(futures):
                future.result()

    run.refresh_from_db()
    run.status = DiscoveryRun.Status.SUCCESS
    run.finished_at = timezone.now()
    run.summary = build_task_result(run)
    run.save(update_fields=["status", "finished_at", "summary"])
    return run.summary


def save_attempts(
    run: DiscoveryRun,
    candidate: DiscoveryCandidate | None,
    attempts: list[DiscoveryAttemptData],
) -> None:
    """Сохранить попытки discovery в базу."""

    DiscoveryAttempt.objects.bulk_create(
        [
            DiscoveryAttempt(
                run=run,
                candidate=candidate,
                ip=attempt.ip,
                method=attempt.method,
                status=attempt.status,
                duration_ms=attempt.duration_ms,
                error=attempt.error[:500],
            )
            for attempt in attempts
        ]
    )


def should_auto_create(profile, candidate: DiscoveryCandidate, dry_run: bool) -> bool:
    """Вернуть True, если кандидата можно автоматически создать как Devices."""

    return bool(
        profile.auto_create
        and not dry_run
        and candidate.status == DiscoveryCandidate.Status.READY
        and candidate.selected_auth_group_id is not None
        and candidate.confidence >= profile.auto_create_min_confidence
    )


def build_task_result(run: DiscoveryRun) -> dict:
    """Построить результат Celery-задачи discovery."""

    return {
        "runId": run.id,
        "taskId": run.task_id,
        "status": run.status,
        "progress": int(run.processed / max(run.total, 1) * 100) if run.total else 0,
        "total": run.total,
        "processed": run.processed,
        "found": run.found,
        "created": run.created,
        "skipped": run.skipped,
        "errors": run.errors,
    }
