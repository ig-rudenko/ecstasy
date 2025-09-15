from functools import reduce
from typing import Optional, Callable, Any


class LazyAttribute:
    default_value: Any = None

    def __set_name__(self, owner, name):
        # print("__set_name__: ", name, owner)
        self.name = "_lazy_" + name
        setattr(owner, self.name, self.default_value)

    def __get__(self, instance, owner):
        # print("__get__: ", self.name, instance.__dir__())
        if hasattr(instance, "_LazyConfigLoader__init_load"):
            getattr(instance, "_LazyConfigLoader__init_load")()
        # print(f"__get__: {self.name}", instance.__dict__.get(self.name))
        return instance.__dict__.get(self.name, self.default_value)

    def __set__(self, instance, value):
        # print(f"__set__: {self.name} = {value}")
        instance.__dict__[self.name] = value


class LazyStringAttribute(LazyAttribute):
    default_value = ""


class LazyIntAttribute(LazyAttribute):
    default_value = 0


class LazyConfigLoader:
    __init_load_function: Optional[Callable[[], Any]] = lambda _: None  # type: ignore

    def __init_load(self):
        """Загрузка настроек Zabbix API из функции"""
        lazy_attrs = list(filter(lambda a: a.startswith("_lazy_"), self.__dir__()))
        # print("lazy_attrs: ", lazy_attrs)
        if not lazy_attrs:
            return
        if (
            self.__init_load_function is not None
            and callable(self.__init_load_function)
            and not reduce(lambda a, b: a and b, map(lambda a: getattr(self, a), lazy_attrs))
        ):
            data = self.__init_load_function()
            self.set_lazy_attributes(data)

    def set_init_load_function(self, func: Callable):
        self.__init_load_function = func

    def set_lazy_attributes(self, data: Any):
        if not data:
            return
        lazy_attrs = list(filter(lambda a: a.startswith("_lazy_"), self.__dir__()))
        for attr in lazy_attrs:
            if isinstance(data, dict):
                if attr.replace("_lazy_", "") in data:
                    setattr(self, attr, data[attr.replace("_lazy_", "")])
                    continue

            if hasattr(data, attr.replace("_lazy_", "")):
                setattr(self, attr, getattr(data, attr.replace("_lazy_", "")))
