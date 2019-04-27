from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

from django.utils.translation import gettext as _
from django.utils.html import mark_safe


# Create your models here.

class Middleware(models.Model):

    name = models.CharField(max_length=50, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))

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


    def save(self):
        from django.core.exceptions import ValidationError
        from .models import DnsNamePattern
        import re

        match = None

        for pattern in DnsNamePattern.objects.all():

            c = re.compile(pattern.regex, re.VERBOSE)
            match = c.match(self.name)

            if match:
                break

        if not match:
            msg = _("The name {0} does not match any of the patterns: {1}".format(self.name,
                        "\n\n".join(DnsNamePattern.objects.all().values_list('regex', flat=True))))
            raise ValidationError(msg)

        super(DnsPoolEntry, self).save()

        data = match.groupdict()

        for category,component in data.items():

            cat, created = DnsNameComponentCategory.objects.get_or_create(category=category)

            if not component and cat.default:
                comp, created = DnsNameComponent.objects.get_or_create(component=cat.default,
                                                            component_category=cat)
            elif component:
                comp, created = DnsNameComponent.objects.get_or_create(component=component,
                                                            component_category=cat)
            comp.dns_pool_entries.add(self)


class DnsNameComponentCategory(models.Model):
    """ A dns entry component describes a part of the dns entry name.
        This class implements the category of the DnsEntry component. """

    category = models.CharField(max_length=50, help_text="The component category of the name")
    default = models.CharField(max_length=50, blank=True, help_text="The default value for category")

    def __str__(self):
        return self.category


class DnsNameComponent(models.Model):
    """ A dns entry component describes a part of the dns entry name.
        This class stores the value of the DnsEntry component and relates to is parent. """

    component_category = models.ForeignKey(DnsNameComponentCategory,
                                           on_delete=models.CASCADE,
                                           verbose_name="Dns Entry Component Category")

    component = models.CharField(max_length=50, unique=True,
                                 help_text="The component value of the name",
                                 verbose_name="Dns Entry Component")

    dns_pool_entries = models.ManyToManyField(DnsPoolEntry,
                                  blank=True,
                                  help_text="Dns Entries that contain this component value",
                                  verbose_name=_("Dns Entries"))

    def __str__(self):
        return self.component


class DnsNameVariation(models.Model):

    variation = models.CharField(max_length=150,
        help_text=_("Concat the naming variation using python format expression e.g ''{type}{farm}foo'"),
        verbose_name=_("DNS Name Variation"))
    description = models.TextField(blank=True, verbose_name=_("Description"))


    def save(self):
        from django.core.exceptions import ValidationError
        from .models import DnsNameComponentCategory
        import re

        valid_subs = list("{{{0}}}".format(c) for c in \
                        DnsNameComponentCategory.objects.all().values_list('category', flat=True))

        wanted_subs = re.findall(r'({\w+})', self.variation)

        if not any(e in wanted_subs for e in valid_subs):
            msg = "Some of this substitutions are not allowed: {0} \
                   Valid Subsitutions are: {1}".format(wanted_subs, ", ".join(valid_subs))
            raise ValidationError(msg)

        super(DnsNameVariation, self).save()

    def __str__(self):
        return self.variation

regex_help_msg = """ A valid named-group regex in python. Verbose expression is allowed. """

class DnsNamePattern(models.Model):

    name = models.CharField(max_length=50, verbose_name=_("Name"))
    regex = models.TextField(help_text=mark_safe(regex_help_msg),
                             verbose_name=_("DNS Entry Name Pattern"))
    description = models.TextField(blank=True, verbose_name=_("Description"))

    variations = models.ManyToManyField(DnsNameVariation,
                                        blank=True,
                                        help_text=_("Ordered list of dns name variations"),
                                        verbose_name=_("Dns Name Variations"))

    def __str__(self):
        return self.name
