import csv

from django.core.management.base import BaseCommand

from gpon.models import SubscriberConnection


class Command(BaseCommand):
    help = "Экспорт GPON подключений абонентов"

    def handle(self, *args, **options):
        qs = (
            SubscriberConnection.objects.all()
            .select_related("customer", "address")
            .prefetch_related(
                "tech_capability__end3__house_olt_states",
                "tech_capability__end3__house_olt_states__statement",
                "tech_capability__end3__house_olt_states__statement__device",
            )
        )

        with open(options["file"], "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Абонент", "Адрес", "Оборудование", "Порт"])
            for conn in qs:
                for olt_state in conn.tech_capability.end3.house_olt_states.all():
                    writer.writerow(
                        [
                            conn.customer,
                            conn.address,
                            olt_state.statement.device,
                            f"{olt_state.statement.olt_port}/{conn.ont_id}",
                        ]
                    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--file",
            type=str,
            help="Имя файла",
            required=True,
        )
