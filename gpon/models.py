from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Address(models.Model):
    region = models.CharField(
        max_length=128,
        verbose_name="Регион",
        default="Севастополь",
    )
    settlement = models.CharField(
        max_length=128,
        verbose_name="Населенный пункт",
        help_text="Любимовка, Верхнесадовое",
        default="Севастополь",
    )
    plan_structure = models.CharField(
        max_length=128,
        verbose_name="ТСН СНТ, СТ",
        help_text="Рыбак-7",
        null=True,
        blank=True,
    )
    street = models.CharField(
        max_length=128,
        verbose_name="Улица",
        help_text="Полное название с указанием типа (улица/проспект/проезд/бульвар/шоссе/переулок/тупик)",
        null=True,
        blank=True,
    )
    house = models.CharField(
        max_length=16,
        validators=[RegexValidator(r"^\d+[а-яА-Я]?$", message="Неверный формат дома")],
        verbose_name="Дом",
        help_text="Можно с буквой (русской)",
    )
    block = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Корпус",
        null=True,
    )
    floor = models.SmallIntegerField(
        verbose_name="Этаж",
        null=True,
    )
    apartment = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Квартира",
        null=True,
    )

    class Meta:
        db_table = "gpon_addresses"

    def __str__(self):
        string = ""
        if self.region != "СЕВАСТОПОЛЬ":
            string += f"{self.region}, "
        if self.settlement != "СЕВАСТОПОЛЬ":
            string += f"{self.settlement}, "
        if self.plan_structure and len(self.plan_structure):
            string += f"СНТ {self.plan_structure}, "
        if self.street and len(self.street):
            string += f"{self.street}, "
        string += f"д. {self.house}"
        if self.block:
            string += f"/{self.block}"

        if self.floor:
            string += f" {self.floor} этаж"
        if self.apartment:
            string += f" кв. {self.apartment}"
        return string

    def __repr__(self):
        return f"Address: ({self.__str__()})"


class OLTState(models.Model):
    """
    Представляет состояние устройства оптического линейного терминала (OLT) в сети GPON, включая связанное
    с ним устройство, порт OLT, оптоволоконное соединение, описание и подключенные к нему дома.
    """

    device = models.ForeignKey("check.Devices", on_delete=models.SET_NULL, null=True)
    olt_port = models.CharField(max_length=24, null=False, blank=False)
    fiber = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    houses = models.ManyToManyField(
        "gpon.HouseB", through="gpon.HouseOLTState", related_name="olt_states"
    )

    class Meta:
        db_table = "gpon_olt_states"


class HouseOLTState(models.Model):
    """
    Представляет состояние дома по отношению к OLT (терминалу оптической линии) в системе GPON.
    """

    house = models.ForeignKey(
        "gpon.HouseB", on_delete=models.CASCADE, blank=False, related_name="house_olt_states"
    )
    statement = models.ForeignKey(
        "gpon.OLTState", on_delete=models.CASCADE, null=True, related_name="house_olt_states"
    )
    entrances = models.CharField(max_length=25, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    end3_set = models.ManyToManyField("gpon.End3", related_name="house_olt_states")

    class Meta:
        db_table = "gpon_house_olt_state"


class HouseB(models.Model):
    """
    Представляет здание с адресом, указывающим, является ли оно многоквартирным или частным, и включает
    информацию о количестве этажей, общем количестве входов и связанных с ним оконечных линий для подключения.
    """

    address = models.ForeignKey(
        "gpon.Address",
        on_delete=models.SET_NULL,
        null=True,
        related_name="buildings",
    )
    apartment_building = models.BooleanField(
        null=False, blank=False, help_text="Многоквартирный дом или частный"
    )
    floors = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        null=False,
        blank=False,
        help_text="кол-во этажей",
    )
    total_entrances = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(255)],
        null=False,
        blank=False,
        help_text="Кол-во подъездов",
    )

    class Meta:
        db_table = "gpon_houses_buildings"


class End3(models.Model):
    """
    Представляет конечную линию в сети GPON с такими атрибутами, как адрес, местоположение, тип и емкость.
    """

    class Type(models.Choices):
        splitter = "splitter"
        rizer = "rizer"

    address = models.ForeignKey(
        "gpon.Address",
        on_delete=models.SET_NULL,
        null=True,
        related_name="end3_set",
    )
    location = models.CharField(max_length=255)
    type = models.CharField(
        choices=Type.choices, max_length=16, verbose_name="Тип оконечного оборудования"
    )
    capacity = models.PositiveSmallIntegerField(
        choices=[(2, 2), (4, 4), (8, 8), (16, 16), (24, 24)], help_text="Кол-во портов/волокон"
    )

    class Meta:
        db_table = "gpon_end3"

    RizerColors = [
        "Синий",
        "Оранжевый",
        "Зеленый",
        "Коричневый",
        "Серый",
        "Белый",
        "Красный",
        "Черный",
        "Желтый",
        "Фиолетовый",
        "Розовый",
        "Бирюзовый",
        "Синие-черный",
        "Оранжево-черный",
        "Зелено-черный",
        "Коричнево-черный",
        "Серо-черный",
        "Бело-черный",
        "Красно-черный",
        "Натуральный(прозрачный)",
        "Желто-черный",
        "Фиолетово-черный",
        "Розово-черный",
        "Бирюзово-черный",
    ]


@receiver(post_save, sender=End3)
def create_tech_capabilities(sender, instance: End3, created: bool, **kwargs):
    """
    Сигнал, который создает техническую возможность на основе мощности и типа оконечной линии.

    :param sender: Параметр `sender` относится к классу модели, который вызвал сигнал.
     В данном случае это модель End3.
    :param instance: Параметр экземпляр является экземпляром модели End3. Он представляет собой объект, вызвавший сигнал
    :param created: Параметр «created» — это логическое значение, которое указывает, был ли экземпляр End3 создан или
     обновлен. Это «True», если экземпляр был создан, и «False», если он был обновлен.
    """
    if not created:
        return

    tech_capability = []

    for i in range(instance.capacity):
        if instance.type == instance.Type.rizer:
            tech_capability.append(TechCapability(end3=instance, rizer_fiber=End3.RizerColors[i]))
        else:
            tech_capability.append(TechCapability(end3=instance, splitter_port=i + 1))

    TechCapability.objects.bulk_create(tech_capability)


class TechCapability(models.Model):
    """
    Класс представляет собой модель хранения технических возможностей,
    связанных с сетью GPON.
    """

    class Status(models.Choices):
        active = "active"
        reserved = "reserved"
        pause = "pause"
        empty = "empty"
        bad = "bad"

    end3 = models.ForeignKey("gpon.End3", on_delete=models.CASCADE)
    status = models.CharField(choices=Status.choices, default=Status.empty.value, max_length=16)
    splitter_port = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(24)],
        null=True,
        verbose_name="Порт на сплиттере",
    )
    rizer_fiber = models.CharField(
        max_length=128, null=True, verbose_name="Цвет волокна на райзере"
    )

    class Meta:
        db_table = "gpon_tech_capabilities"

    @property
    def ending(self) -> str:
        return str(self.splitter_port or self.rizer_fiber)


class Customer(models.Model):
    """Определяет модель для клиента"""

    class Type(models.Choices):
        person = "person"
        company = "company"
        contract = "contract"

    type = models.CharField(choices=Type.choices, max_length=128, null=False, blank=False)
    company_name = models.CharField(max_length=256, null=True, blank=True)
    first_name = models.CharField(max_length=256, null=True, blank=True)
    surname = models.CharField(max_length=256, null=True, blank=True)
    last_name = models.CharField(max_length=256, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    contract = models.CharField(max_length=128)

    class Meta:
        db_table = "gpon_customers"

    @property
    def full_name(self) -> str:
        name = ""
        if self.surname or self.first_name or self.last_name:
            name += f"{self.surname} {self.first_name} {self.last_name} "
        if self.company_name:
            name += f"{self.company_name}"
        return name.strip()


class Service(models.Model):
    name = models.CharField(max_length=128)

    class Meta:
        db_table = "gpon_services"


class SubscriberConnection(models.Model):
    """
    Представляет абонентское подключение с различными атрибутами, такими как адрес,
    технологические возможности, IP, идентификатор ONT, последовательный порт ONT,
    MAC-адрес ONT, наряд, транзит, подключение и услуги.
    """

    address = models.ForeignKey(
        "gpon.Address", on_delete=models.SET_NULL, null=True, related_name="subscribers"
    )
    customer = models.ForeignKey(
        "gpon.Customer", related_name="connections", on_delete=models.CASCADE
    )
    tech_capability = models.ForeignKey(
        "gpon.TechCapability",
        on_delete=models.SET_NULL,
        null=True,
        related_name="subscriber_connection",
    )

    ip = models.GenericIPAddressField(protocol="ipv4", null=True)

    ont_id = models.PositiveSmallIntegerField(null=False, blank=False)
    ont_serial = models.CharField(max_length=128, null=True)
    ont_mac = models.CharField(max_length=12, null=True)

    order = models.CharField(max_length=128, null=True)
    transit = models.PositiveIntegerField(null=True)
    connected_at = models.DateTimeField(null=True)
    services = models.ManyToManyField("gpon.Service", related_name="subscribers")
