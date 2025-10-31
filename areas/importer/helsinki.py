import logging
import urllib

from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.gdal.feature import Feature
from django.db import transaction

from areas.models import ContractZone
from haravajarjestelma.settings import EXCLUDED_CONTRACT_ZONES

from .utils import ModelSyncher

logger = logging.getLogger(__name__)


class HelsinkiImporter:
    def import_contract_zones(self, force=False):
        logger.info("Importing Helsinki contract zones")

        data_source = self._fetch_contract_zones()
        self._process_contract_zones(data_source, force)

        logger.info("Helsinki contract zone import done!")

    def _fetch_contract_zones(self):
        contract_zone_filter_str = (
            ' AND "nimi" NOT IN ({})'.format(
                ",".join(f"'{cz}'" for cz in EXCLUDED_CONTRACT_ZONES)
            )
            if EXCLUDED_CONTRACT_ZONES
            else ""
        )
        query_params = {
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "GetFeature",
            "TYPENAME": "Vastuualue_rya_urakkarajat",
            "SRSNAME": f"EPSG:{settings.DEFAULT_SRID}",
            "cql_filter": (
                "tehtavakokonaisuus='PUISTO' AND "
                f"status='voimassa'{contract_zone_filter_str}"
            ),
            "outputFormat": "application/json",
        }
        wfs_url = (
            f"{settings.HELSINKI_WFS_BASE_URL}?{urllib.parse.urlencode(query_params)}"
        )

        logger.debug(f"Fetching contract zone data from url {wfs_url}")
        data_source = DataSource(wfs_url)
        logger.debug(f"Fetched {len(data_source[0])} active contract zones")

        return data_source

    @transaction.atomic
    def _process_contract_zones(self, data_source, force=False):
        layer = data_source[0]
        syncher = ModelSyncher(
            ContractZone.objects.all(), lambda x: x.name, self._deactivate_contract_zone
        )

        for feat in layer:
            data = {
                "name": str(feat["nimi"]),
                "boundary": feat.geom.geos,
                "contractor": self._get_attribute_safe(feat, "urakoitsija"),
                "contact_person": self._get_attribute_safe(feat, "talkoot"),
                "email": self._get_attribute_safe(feat, "talkoot_email"),
                "phone": self._get_attribute_safe(feat, "talkoot_puh"),
                "secondary_contact_person": self._get_attribute_safe(
                    feat, "talkoot_varahlo"
                ),
                "secondary_email": self._get_attribute_safe(
                    feat, "talkoot_varahlo_email"
                ),
                "secondary_phone": self._get_attribute_safe(
                    feat, "talkoot_varahlo_puh"
                ),
                "origin_id": str(feat["id"]),
                "active": True,
            }

            contract_zone = syncher.get(data["name"])
            if contract_zone:
                logger.info(
                    "Updating contract zone {} (id {})".format(
                        data["name"], data["origin_id"]
                    )
                )
                for field, new_value in data.items():
                    setattr(contract_zone, field, new_value)
            else:
                logger.info(
                    "Creating new contract zone {} (id {})".format(
                        data["name"], data["origin_id"]
                    )
                )
                contract_zone = ContractZone(**data)

            contract_zone.save()
            syncher.mark(contract_zone)

        syncher.finish(force=force)

    @staticmethod
    def _get_attribute_safe(feature: Feature, attribute):
        try:
            value = feature.get(attribute)
        except IndexError:
            value = None
        return str(value).strip() if value is not None else ""

    @staticmethod
    def _deactivate_contract_zone(contract_zone):
        if contract_zone.active:
            contract_zone.active = False
            contract_zone.save(update_fields=("active",))
