from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

from django.utils.translation import gettext as _
from django.utils.html import mark_safe


# Create your models here.

class Middleware(models.Model):

    name = models.CharField(max_length=50, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    identifier = models.CharField(max_length=5,
                help_text=_("Identifier for this middleware"))

    def __str__(self):
        return self.name


class SubnetParent(MPTTModel):
    """ this implements
        all organisation units of the network topology
        that are possible in the customer environment.
        Possible units are NetworkZone, PhysicalNetworkZone and DatacenterLocation
        """
    name = models.CharField(max_length=50, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='subnet_parents',
                            on_delete=models.CASCADE, db_index=True, verbose_name=_("Subnet-Parent"))

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        ancestors = self.get_ancestors(include_self=True)
        return " - ".join(ancestors.values_list('name', flat=True))


class Subnet(models.Model):
    """ this is the model managing the subnets in a hierarchical
        structure. This structure adapts the network topology
        of the network environment of the cutomer side.
        """

    cidr = models.CharField(max_length=50, verbose_name=_("Name"))
    parent = TreeForeignKey(SubnetParent, null=True, blank=True, on_delete=models.CASCADE,
                            related_name='subnets', db_index=True, verbose_name=_("Subnet-Parent"))


    admin = models.BooleanField(default=False,
                    help_text=_("Does policy allow to use this subnet for administrative purpose"),
                                verbose_name=_("Admin Subnet"))

    middlewares = models.ManyToManyField(Middleware, blank=True,
                                    help_text=_("Middlewares configured for this subnet"),
                                    verbose_name=_("Middlewares"))

    def __str__(self):
        return self.cidr


class DnsEntry(models.Model):

    name = models.CharField(max_length=50, verbose_name=_("Name"))
    address = models.GenericIPAddressField(help_text=_("The ip address of the name entry"),
                                           verbose_name=_("IP-Address"))
    subnet = models.ForeignKey(Subnet, on_delete=models.CASCADE,
                               help_text=_("The subnet this ip address belongs to."),
                               verbose_name=_("Dns Entry"))

    class Meta:
        verbose_name_plural = _("Dns Entries")

    def __str__(self):
        return self.name


class DnsPoolEntry(models.Model):

    name = models.CharField(max_length=50, verbose_name=_("Name"))
    entries = models.ManyToManyField(DnsEntry, blank=True, verbose_name=_("Dns-Entries"))

    class Meta:
        verbose_name_plural = _("Dns PoolEntries")

    def __str__(self):
        return self.name
