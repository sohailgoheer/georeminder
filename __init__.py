def classFactory(iface):
    from .georeminder import GeoReminder
    return GeoReminder(iface)

