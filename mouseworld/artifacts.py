from dataclasses import dataclass, field, asdict
from abc import ABC
# from typing import Optional

@dataclass
class Device(ABC):
    "Generic class to describe an object"
    id: str = field(repr=False)
    name: str
    description: str = ""
    version: str = field(default="1")


@dataclass
class Conection(ABC):
    """Generic class that defines a conection"""
    name: str
    internal_cp: None
    external_cp: None

    # def __post_init__(self):
    #     self.internal_cp = f"{self.device_name}_{self.vld}"


@dataclass
class NSTConection(Conection):
    """Class that defines a conection between a NST and a NSD"""


@dataclass
class NSDConection(Conection):
    """Class that defines a conection between a NSD and a VNF"""
    mgmt: bool = False


@dataclass
class VNFConection(Conection):
    """Class that defines conections in a VNF"""


@dataclass
class VDU(Device):
    """Class that defines a VDU"""


@dataclass
class VNF(Device):
    """Class that defines a VNF"""
    vdus: list[VDU] = field(repr=False, default_factory=list)
    vnfConections: list[VNFConection] = field(default_factory=list)


@dataclass
class NSD(Device):
    """Class that defines a NSD"""
    nsdConections: list[NSDConection] = field(default_factory=list)
    vnfs: list[VNF] = field(repr=False, default_factory=list)


@dataclass
class NST(Device):
    """Class that defines a NST"""
    nstConections: list[NSTConection] = None
    nsds: list[NSD] = field(repr=False, default_factory=list)


if __name__ == "__main__":
    vnf1 = VNF(id="vnf1", name="vnf1")
    nsdcx1 = NSDConection(vld="management_network", mgmt= True, device_name=vnf1.name)
    nsd = NSD(id="ns1", name="ns1", nsdConections=[nsdcx1], vnfs=vnf1)

    print(nsd)