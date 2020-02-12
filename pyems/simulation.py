import tempfile
from typing import List
import numpy as np
from openEMS import openEMS
from CSXCAD.CSXCAD import ContinuousStructure
from pyems.network import Network
from pyems.field_dump import FieldDump


class Simulation:
    """
    OpenEMS simulation.  This is the main entry-point for
    creating/running a simulation.
    """

    def __init__(
        self,
        fdtd: openEMS,
        csx: ContinuousStructure,
        center_freq: float,
        half_bandwidth: float,
        boundary_conditions: List[str],
        network: Network = None,
        field_dumps: List[FieldDump] = None,
    ):
        """
        """
        self.fdtd = fdtd
        self.csx = csx
        self.fdtd.SetCSX(self.csx)
        self.center_freq = center_freq
        self.half_bandwidth = half_bandwidth
        self.fdtd.SetGaussExcite(center_freq, half_bandwidth)
        self.fdtd.SetBoundaryCond(boundary_conditions)
        self.network = network
        self.field_dumps = field_dumps

    def set_network(self, network: Network) -> None:
        """
        """
        self.network = network

    def get_network(self) -> Network:
        return self.network

    def add_field_dump(self, field_dump: FieldDump) -> None:
        """
        """
        self.field_dumps.append(field_dump)

    def set_field_dumps(self, field_dumps: List[FieldDump]) -> None:
        """
        """
        self.field_dumps = field_dumps

    def get_field_dumps(self) -> List[FieldDump]:
        """
        """
        return self.field_dumps

    def finalize_structure(self, expand_bounds: List[float]) -> None:
        self.network.generate_mesh(
            lambda_min=freq_wavelength(self.center_freq + self.half_bandwidth),
            expand_bounds=expand_bounds,
        )

    def simulate(self, num_freq_bins: int = 501) -> None:
        """
        """
        freq_bins = np.linspace(
            self.center_freq - self.half_bandwidth,
            self.center_freq + self.half_bandwidth,
            num_freq_bins,
        )
        tmpdir = tempfile.mkdtemp()
        self.fdtd.Run(tmpdir, cleanup=True)
        self.network.calc(sim_dir=tmpdir, freq=freq_bins)

    def view_network(self) -> None:
        """
        View the simulation network.
        """
        self.network.view()

    def save_network(self, file_path: str) -> None:
        """
        Save the network to a file.

        :param file_path: The path where the network should be saved.
        """
        self.network.save(file_path=file_path)

    def view_field(self, index: int = 0) -> None:
        """
        View a field dump.

        :param index: The index of the field dump to view from the
            list of field dumps retreived by `get_field_dumps`.  This
            defaults to the first field dump if an index is not
            provided.
        """
        self.field_dumps[index].view()

    def save_field(self, dir_path: str, index: int = 0) -> None:
        """
        Save a field dump to a file.

        :param file_path: Directory path in which field dumps will be
            saved.
        :param index: The index of the field dump in `get_field_dumps`
            to save.  If this argument is ommitted, it defaults to the
            first field dump.
        """
        self.field_dumps[index].save(dir_path=dir_path)


def freq_wavelength(freq: float) -> float:
    """
    Calculate the wavelength for a given frequency of light.  This
    presently assumes that the light is travelling through a vacuum.
    """
    return 299792458 / freq


def sweep(simulations: List[Simulation], function_object):
    """
    Dispatch a number of simulations and then apply a function to each
    simulation after completion.  The function must take a single
    `Simulation` as an argument and return the result of interest.

    :param simulations: A list of simulation objects to simulate and
        then process with `function_object`.  It is up to the caller
        to ensure that these simulation objects differ from one
        another in the desired way.
    :param function_object: The function object to apply to each
        simulation after that simulation has completed.

    :returns: A list where each entry is the return value of
              `function_object` applied to a single simulation from
              `simulations`.  The order between returned values and
              input simulations is preserved.  That is, the first item
              in the return value list corresponds to
              `simulations[0]`, etc.
    """