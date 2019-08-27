from django.db import models
from django.utils.translation import gettext as _

# Create your models here.


class NameEntry(models.Model):

    name = models.CharField(max_length=50, verbose_name=_("Name"))

    class Meta:
        verbose_name_plural = _("Name Entries")

    def __str__(self):
        return self.name


class PoolType(models.Model):
    """ a name pool type defines the
        type that a named pool entry belongs. """

    name = models.CharField(max_length=50, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))


class NamePoolEntry(models.Model):
    """ a name pool entry describes a classified
        name entry that belongs to a specific pool."""

    name = models.CharField(max_length=50, verbose_name=_("Name"))
    entries = models.ManyToManyField(NameEntry, blank=True, verbose_name=_("Entries"))
    pool_type = models.ForeignKey(PoolType, on_delete=models.CASCADE,
                                  verbose_name=_("Name Pool Type"))

    class Meta:
        verbose_name_plural = _("Name Pool Entries")

    def __str__(self):
        return self.name

    def save(self):
        """ validate the name against all existing name patterns
            of a pool type and saves the entry and all its artifacts. """

        from django.core.exceptions import ValidationError
        from .models import NamePattern
        import re

        match = None

        for pattern in NamePattern.objects.find(pool_type=pool_type):

            c = re.compile(pattern.regex, re.VERBOSE)
            match = c.match(self.name)

            if match:
                break

            if not match:
                msg = _("The name {0} does not match any of the patterns: {1}".format(self.name,
                            "\n\n".join(NamePattern.objects.all().values_list('regex', flat=True))))
                raise ValidationError(msg)


        super(NamePoolEntry, self).save()

        data = match.groupdict()

        for c,a in data.items():

            criteria, created = NamingArtifactsCriteria.objects.get_or_create(criteria=c)

            if not a and criteria.default:
                artifact, created = NamingArtifacts.objects.get_or_create(
                    artifact=criteria.default,
                    criteria=c)
            elif a:
                artifact, created = NamingArtifacts.objects.get_or_create(
                    artifact=a,
                    criteria=c)

            artifact.dns_pool_entries.add(self)


class NamingArtifactsCriteria(models.Model):
    """ A naming artifact describes a part of a name entry.
        This class defines the criteria of the entry artifact. """

    criteria = models.CharField(max_length=50, help_text="The artifact criteria of the name")
    default = models.CharField(max_length=50, blank=True, help_text="The default value for criteria")

    def __str__(self):
        return self.criteria


class NamingArtifacts(models.Model):
    """ A entry artifact describes a part of the entry name.
        This class stores the value of the entry artifact and relates to is parent. """

    criteria = models.ForeignKey(NamingArtifactsCriteria,
                                           on_delete=models.CASCADE,
                                           verbose_name="NameEntry Criteria")

    artifact = models.CharField(max_length=50, unique=True,
                                 help_text="The artifact value of the name",
                                 verbose_name="NameEntry Component")

    related_entries = models.ManyToManyField(NamePoolEntry,
                                  blank=True,
                                  help_text=" Entries that contain this artifact",
                                  verbose_name=_("NameEntries"))

    def __str__(self):
        return self.artifact


class NamingScheme(models.Model):
    """ a naming scheme is extracted of the named group pattern and
        can be used as python format substition to create new variations of the
        name by following a naming scheme.
        """

    scheme = models.CharField(max_length=150,
        help_text=_("Concat the naming scheme using python format expression e.g ''{type}{farm}foo'"),
        verbose_name=_("Name Scheme"))
    description = models.TextField(blank=True, verbose_name=_("Description"))


    def save(self):
        from django.core.exceptions import ValidationError
        from .models import NamingArtifactsCriteria
        import re

        valid_subs = list("{{{0}}}".format(c) for c in \
                        NamingArtifactsCriteria.objects.all().values_list('criteria', flat=True))

        wanted_subs = re.findall(r'({\w+})', self.scheme)

        if not any(e in wanted_subs for e in valid_subs):
            msg = "Some of this substitutions are not allowed: {0} \
                   Valid Subsitutions are: {1}".format(wanted_subs, ", ".join(valid_subs))
            raise ValidationError(msg)

        super(NamingScheme, self).save()

    def __str__(self):
        return self.scheme


class NamePattern(models.Model):
    """ The name pattern identifies a
        classified name that should belong to the pool.
        A name identified to the pattern should be saved
        to pool with the pool criteria of the pattern. """

    name = models.CharField(max_length=50, verbose_name=_("Name"))
    regex = models.TextField(verbose_name=_("DNS Entry Name Pattern"),
        help_text=_("named group regex in python verbose expression"))
    description = models.TextField(blank=True, verbose_name=_("Description"))

    criteria = models.ForeignKey(PoolType, on_delete=models.CASCADE,
                                 verbose_name=_("Pool Criteria"))

    schemes = models.ManyToManyField(NamingScheme,
                                        blank=True,
                                        help_text=_("Ordered list of naming schemes"),
                                        verbose_name=_("Naming Schemes"))

    def __str__(self):
        return self.name
