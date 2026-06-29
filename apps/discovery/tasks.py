from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import DiscoveryAttempt, DiscoveryCandidate, DiscoveryProfile, DiscoveryRun
from .services.dataclasses import DeviceFingerprint, DiscoveryAttemptData
from .services.fingerprint import DeviceFingerprinter
from .services.provisioning import accept_candidate
from .services.reconcile import upsert_candidate
from .services.scanner import build_scan_hosts, preflight_address

DISCOVERY_PROGRESS_UPDATE_INTERVAL = 10
FINISHED_DISCOVERY_STATUSES = (
    DiscoveryRun.Status.SUCCESS,
    DiscoveryRun.Status.FAILURE,
    DiscoveryRun.Status.REVOKED,
)


@dataclass(slots=True)
class DiscoveryScanResult:
    """Результат сетевого опроса одного IP без операций с БД."""

    ip: str
    attempts: list[DiscoveryAttemptData]
    fingerprint: DeviceFingerprint | None = None
    skipped: bool = False
    error: str = ""


@shared_task(name="discovery_run_task", ignore_result=True)
def run_discover_profile(dis_prof_id: int):
    try:
        dis_profile = DiscoveryProfile.objects.get(pk=dis_prof_id)
    except DiscoveryProfile.DoesNotExist:
        return

    if not dis_profile.is_active:
        return

    run = DiscoveryRun.objects.create(profile=dis_profile, created_by=None, dry_run=False)
    discovery_run_task(run.id, dis_profile.networks)


@shared_task(bind=True)
def discovery_run_task(self, run_id: int, networks_override: list[str] | None = None) -> dict:
    """Выполнить auto discovery run в фоне."""

    run = (
        DiscoveryRun.objects.select_related("profile", "profile__device_group")
        .prefetch_related("profile__auth_groups")
        .get(id=run_id)
    )
    profile = run.profile
    auth_groups = list(profile.auth_groups.all())
    counters = {"processed": 0, "found": 0, "created": 0, "skipped": 0, "errors": 0}

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
        """Периодически сохранить прогресс discovery одним DB-потоком."""

        counters["processed"] += 1
        if counters["processed"] < len(hosts) and counters["processed"] % DISCOVERY_PROGRESS_UPDATE_INTERVAL:
            return

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

    def scan_ip(ip: str) -> DiscoveryScanResult:
        """Выполнить только сетевой опрос IP без обращения к Django ORM."""

        attempts: list[DiscoveryAttemptData] = []
        try:
            detected_protocols, preflight_attempts = preflight_address(
                ip,
                protocols=profile.try_protocols or ["ssh", "telnet"],
                timeout=profile.timeout_seconds,
            )
            attempts.extend(preflight_attempts)
            if not any(detected_protocols.values()):
                return DiscoveryScanResult(ip=ip, attempts=attempts, skipped=True)

            fingerprint, fingerprint_attempts = DeviceFingerprinter(
                profile,
                auth_groups=auth_groups,
                include_cli=True,
            ).collect(
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

            return DiscoveryScanResult(ip=ip, attempts=attempts, fingerprint=fingerprint)
        except Exception as exc:
            attempts.append(
                DiscoveryAttemptData(
                    ip=ip,
                    method=DiscoveryAttempt.Method.PING,
                    status=DiscoveryAttempt.Status.FAILED,
                    error=str(exc)[:500],
                )
            )
            return DiscoveryScanResult(
                ip=ip,
                attempts=attempts,
                error=str(exc)[:500],
            )

    def persist_result(result: DiscoveryScanResult) -> None:
        """Последовательно сохранить результат сетевого опроса в БД."""

        candidate = None
        try:
            if result.error:
                counters["errors"] += 1
                save_attempts(run, None, result.attempts)
                return
            if result.skipped:
                counters["skipped"] += 1
                save_attempts(run, None, result.attempts)
                return
            if result.fingerprint is None:
                raise ValueError(f"Отсутствует fingerprint для {result.ip}")

            candidate = upsert_candidate(result.fingerprint)
            save_attempts(run, candidate, result.attempts)
            counters["found"] += 1

            if should_auto_create(profile, candidate, run.dry_run):
                accept_candidate(candidate, profile=profile, collect_interfaces=False)
                counters["created"] += 1
        except Exception as exc:
            counters["errors"] += 1
            if candidate is not None:
                candidate.last_error = str(exc)[:500]
                candidate.save(update_fields=["last_error"])
            save_attempts(
                run,
                candidate,
                [
                    DiscoveryAttemptData(
                        ip=result.ip,
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
            persist_result(scan_ip(ip))
    else:
        with ThreadPoolExecutor(max_workers=workers_count) as executor:
            futures = [executor.submit(scan_ip, ip) for ip in hosts]
            for future in as_completed(futures):
                persist_result(future.result())

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


@shared_task(name="cleanup_discovery_runs_task")
def cleanup_discovery_runs_task(retention_days: int) -> dict:
    """Удалить старые завершенные discovery runs вместе с attempts."""

    retention_days = int(retention_days)
    if retention_days < 1:
        raise ValueError("retention_days must be positive")

    cutoff = timezone.now() - timedelta(days=retention_days)
    old_runs = DiscoveryRun.objects.filter(status__in=FINISHED_DISCOVERY_STATUSES, finished_at__lt=cutoff)
    deleted_runs = old_runs.count()
    old_runs.delete()
    return {
        "deletedRuns": deleted_runs,
        "retentionDays": retention_days,
    }
